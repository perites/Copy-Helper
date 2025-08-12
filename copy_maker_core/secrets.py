import dataclasses


@dataclasses.dataclass
class Secrets:
    def __init__(self):
        self.oauth_client = None
        self.monday_token = None
        self.credentials = None
        self.callable_update_credentials = None


secrets = Secrets()
