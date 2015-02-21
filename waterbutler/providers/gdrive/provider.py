import json
import asyncio

import furl

from waterbutler.core import utils
from waterbutler.core import streams
from waterbutler.core import provider
from waterbutler.core import exceptions

from waterbutler.providers.gdrive import settings
from waterbutler.providers.gdrive.metadata import GoogleDriveRevision
from waterbutler.providers.gdrive.metadata import GoogleDriveFileMetadata
from waterbutler.providers.gdrive.metadata import GoogleDriveFolderMetadata


class GoogleDrivePath(utils.WaterButlerPath):

    def __init__(self, path, prefix=True, suffix=False):
        super().__init__(path, prefix=prefix, suffix=suffix)


class GoogleDriveProvider(provider.BaseProvider):

    BASE_URL = settings.BASE_URL

    def __init__(self, auth, credentials, settings):
        super().__init__(auth, credentials, settings)
        self.token = self.credentials['token']
        self.folder = self.settings['folder']

    @property
    def default_headers(self):
        return {'authorization': 'Bearer {}'.format(self.token)}

    @asyncio.coroutine
    def download(self, path, revision=None, **kwargs):
        data = yield from self.metadata(path, raw=True)
        # TODO: Add map from document type to export url key @kushg
        try:
            download_url = data['downloadUrl']
        except KeyError:
            download_url = data['exportLinks']['application/pdf']
        download_resp = yield from self.make_request(
            'GET',
            download_url,
            expects=(200, ),
            throws=exceptions.DownloadError,
        )

        return streams.ResponseStreamReader(download_resp)

    @asyncio.coroutine
    def upload(self, stream, path, **kwargs):
        path = GoogleDrivePath(path)
        try:
            metadata = yield from self.metadata(str(path), raw=True)
            folder_id = metadata['parents'][0]['id']
            segments = (metadata['id'], )
            created = False
        except:
            parent_path = str(path.parent).rstrip('/')
            metadata = yield from self.metadata(parent_path, raw=True)
            folder_id = metadata['id']
            segments = ()
            created = True
        upload_metadata = {
            'parents': [
                {
                    'kind': 'drive#parentReference',
                    'id': folder_id,
                },
            ],
            'title': path.name,
        }
        resp = yield from self.make_request(
            'POST' if created else 'PUT',
            self._build_upload_url('files', *segments, uploadType='resumable'),
            headers={
                'Content-Type': 'application/json',
                'X-Upload-Content-Length': str(stream.size),
            },
            data=json.dumps(upload_metadata),
            expects=(200, ),
            throws=exceptions.UploadError,
        )
        location = furl.furl(resp.headers['LOCATION'])
        upload_id = location.args['upload_id']
        resp = yield from self.make_request(
            'PUT',
            self._build_upload_url('files', *segments, uploadType='resumable', upload_id=upload_id),
            headers={'Content-Length': str(stream.size)},
            data=stream,
            expects=(200, ),
            throws=exceptions.UploadError,
        )
        data = yield from resp.json()
        return GoogleDriveFileMetadata(data, path.parent).serialized(), created

    @asyncio.coroutine
    def delete(self, path, **kwargs):
        path = GoogleDrivePath(path, self.folder)
        metadata = yield from self.metadata(str(path), raw=True)
        yield from self.make_request(
            'DELETE',
            self.build_url('files', metadata['id']),
            expects=(204, ),
            throws=exceptions.DeleteError,
        )

    def _serialize_item(self, path, item, raw=False):
        if raw:
            return item
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            return GoogleDriveFolderMetadata(item, path).serialized()
        return GoogleDriveFileMetadata(item, path).serialized()

    @asyncio.coroutine
    def metadata(self, path, original_path=None, folder_id=None, raw=False, **kwargs):
        path = GoogleDrivePath(path, self.folder)
        original_path = original_path or path
        folder_id = folder_id or self.folder['id']
        child = path.child

        queries = [
            "'{}' in parents".format(folder_id),
            'trashed = false',
        ]
        if not path.is_leaf and not path.is_dir:
            queries.append("title = '{}'".format(child.parts[1]))
        query = ' and '.join(queries)

        resp = yield from self.make_request(
            'GET',
            self.build_url('files', q=query, alt='json'),
            expects=(200, ),
            throws=exceptions.MetadataError,
        )
        data = yield from resp.json()

        if (path.is_dir and not path.is_leaf) or (path.is_file and not child.is_leaf):
            child_id = data['items'][0]['id']
            return (yield from self.metadata(str(child), original_path=original_path, folder_id=child_id, raw=raw, **kwargs))

        if path.is_dir:
            return [
                self._serialize_item(original_path, item, raw=raw)
                for item in data['items']
            ]
        return self._serialize_item(original_path.parent, data['items'][0], raw=raw)

    @asyncio.coroutine
    def revisions(self, path, **kwargs):
        metadata = yield from self.metadata(path, raw=True)
        response = yield from self.make_request(
            'GET',
            self.build_url('files', metadata['id'], 'revisions'),
            expects=(200, ),
            throws=exceptions.RevisionsError,
        )
        data = yield from response.json()
        return [
            GoogleDriveRevision(item).serialized()
            for item in reversed(data['items'])
        ]

    def _build_upload_url(self, *segments, **query):
        return provider.build_url(settings.BASE_UPLOAD_URL, *segments, **query)
