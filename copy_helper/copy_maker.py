from . import domain
from . import copy


class CopyMaker:
    def __init__(self, domain_name, str_copy, bc_date):
        self.domain = domain.Domain(domain_name)
        self.copy = copy.Copy.create(str_copy)
        self.date = bc_date.replace('/', '.')
