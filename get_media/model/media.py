from datetime import datetime
from typing import Optional, List

from dataclasses import dataclass

from get_media.model.source import Source


@dataclass
class Owner:
    id: str
    avatar: str
    username: str
    birthday: int
    countLike: int
    countView: int
    countFollow: int
    countFollowBy: int
    countMedia: int


@dataclass
class InstagramMedia:
    shortcode: str
    height: int
    width: int
    thumbnail: str
    countLike: int
    countView: int
    countComment: int


@dataclass
class InstagramProfile:
    owner: Owner
    data: List[InstagramMedia]


@dataclass
class Media:
    link: str
    source: Source
    url: str
    extractData: Optional[InstagramProfile, InstagramMedia]
    _expire_at: datetime
