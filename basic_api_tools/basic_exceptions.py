class BasicRequestException(Exception):
    def __init__(self, msg, status_code=400):
        self.status_code = status_code
        super().__init__(msg)


class CredentialsMissing(BasicRequestException):
    def __init__(self):
        message = 'Missing credentials in request body'
        super().__init__(message, 401)


class RequiredFieldMissing(BasicRequestException):
    def __init__(self, field_name, field_where_missing):
        message = f'Missing required field {field_name} in {field_where_missing}'
        super().__init__(message)


class WrongFieldType(BasicRequestException):
    def __init__(self, value_type, field_name):
        message = f'Wrong field type, expected dict got {value_type} for field {field_name}'
        super().__init__(message)
