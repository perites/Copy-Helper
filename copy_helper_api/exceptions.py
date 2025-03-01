class BasicGoogleServiceException(Exception):
    def __init__(self, msg, status_code=500):
        self.status_code = status_code
        super().__init__(msg)


class UnsupportedFileType(BasicGoogleServiceException):
    def __init__(self, type_name):
        message = f'Unsupported file mimeType {type_name}'
        super().__init__(message, 400)
