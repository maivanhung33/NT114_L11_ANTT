from dataclasses import dataclass


@dataclass
class Collection:
    _id: str
    ownerPhone: str
    name: str
