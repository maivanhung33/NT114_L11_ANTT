from dataclasses import dataclass


@dataclass
class CollectionItem:
    collectionId: str
    ownerPhone: str
    id: str
    url: str
    type: str
    thumbnail: str
    platform: str
    source: str
