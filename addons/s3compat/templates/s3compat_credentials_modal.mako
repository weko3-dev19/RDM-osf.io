<div id="s3compatInputCredentials" class="modal fade">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">

            <div class="modal-header">
                <h3>Connect an S3 Compatible Storage Account</h3>
            </div>

            <form>
                <div class="modal-body">

                    <div class="row">
                        <div class="col-sm-3"></div>

                        <div class="col-sm-6">
                            <div class="form-group">
                                <label for="s3compatAddon">S3 Compatible Service</label>
                                <select class="form-control" data-bind="value: selectedService, options: availableServices, optionsText: 'name'" id="selected_service" name="selected_service" ${'disabled' if disabled else ''}></select>
                            </div>
                            <div class="form-group">
                                <label for="s3compatAddon">Access Key</label>
                                <input class="form-control" data-bind="value: accessKey" name="access_key" ${'disabled' if disabled else ''} />
                            </div>
                            <div class="form-group">
                                <label for="s3compatAddon">Secret Key</label>
                                <input type="password" class="form-control" data-bind="value: secretKey" name="secret_key" ${'disabled' if disabled else ''} />
                            </div>
                        </div>
                    </div><!-- end row -->

                    <!-- Flashed Messages -->
                    <div class="help-block">
                        <p data-bind="html: message, attr: {class: messageClass}"></p>
                    </div>

                </div><!-- end modal-body -->

                <div class="modal-footer">

                    <a href="#" class="btn btn-default" data-bind="click: clearModal" data-dismiss="modal">Cancel</a>

                    <!-- Save Button -->
                    <button data-bind="click: connectAccount" class="btn btn-success">Save</button>

                </div><!-- end modal-footer -->

            </form>

        </div><!-- end modal-content -->
    </div>
</div>
