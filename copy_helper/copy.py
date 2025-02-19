import dataclasses
from . import offer

import re

import logging


@dataclasses.dataclass
class Copy:
    offer: offer.Offer
    lift_number: str
    img_code: str

    @classmethod
    def create(cls, str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            logging.debug(f'Failed to find offer name, lift_number and img_code in {str_copy}')
            return None

        return cls(offer.Offer(match.group(1)), match.group(2), match.group(3))

    def __str__(self):
        return self.offer.name + self.lift_number + self.img_code
