<div class="project-authors" style="padding: 0 10px 10px 10px;">
    % for contributor in contributors:
        <div mod-meta='{
                "tpl": "util/render_user.mako",
                "uri": "/api/v1/profile/${contributor['user_id']}/summary/",
                "view_kwargs": {
                    "formatter": "surname"
                },
                "replace": true
        }'>
        </div>
        <span>${contributor['separator']}</span>
    % endfor
    % if others_count:
        <a href="${node_url}">${others_count} other${others_suffix}</a>
    % endif
</div>