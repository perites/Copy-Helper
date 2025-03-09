class BasicGoogleServiceException(Exception):
    def __init__(self, msg, status_code=500):
        self.status_code = status_code
        super().__init__(msg)


class UnsupportedFileType(BasicGoogleServiceException):
    def __init__(self, type_name):
        self.message = f'Unsupported file mimeType {type_name}'
        super().__init__(self.message, 400)


class BasicDomainException(Exception):
    def __init__(self, msg, status_code=500):
        self.status_code = status_code
        super().__init__(msg)


class DomainNotFound(BasicDomainException):
    def __init__(self, domain_name):
        self.message = f'Could not find domain {domain_name} in Broadcast'
        super().__init__(self.message, 500)


class DateNotFound(BasicDomainException):
    def __init__(self, date):
        self.message = f'Could not find date {date} in Broadcast'
        super().__init__(self.message, 400)


class CopyNotFound(BasicDomainException):
    def __init__(self, copies_range):
        self.message = f'Could not find copies in range {copies_range} in Broadcast'
        super().__init__(self.message)
