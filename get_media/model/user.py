from typing import List

from dataclasses import dataclass

from get_media.model.source import Source


@dataclass
class FavoriteItem:
    url: str
    type: str
    source: Source


@dataclass
class User:
    username: str
    password: str
    lastName: str
    firstName: str
    birthday: int
    phone: str
    email: str
    avatar: str
    favorites: List[FavoriteItem]
