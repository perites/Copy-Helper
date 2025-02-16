class OfferWasNotFoundError(Exception):
    def __init__(self, offer_name):
        self.message = f'Offer {offer_name} was not found at backend'
        super().__init__(self.message)


class NoPartnersWithOffer(Exception):
    def __init__(self, offer_name):
        self.message = f'No Partners with offer {offer_name} was not found in GoogleDrive'
        super().__init__(self.message)


class SettingsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
