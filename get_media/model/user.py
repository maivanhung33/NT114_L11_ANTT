from dataclasses import dataclass
from typing import List

from get_media.model.source import Source


@dataclass
class FavoriteItem:
    url: str
    type: str
    source: Source


@dataclass
class User:
    password: str
    lastname: str
    firstname: str
    birthday: int
    favorites: List[FavoriteItem]
    phone: str
    verified: bool = False
    avatar: str = None
    email: str = None
