from dataclasses import dataclass


@dataclass
class User:
    password: str
    lastname: str
    firstname: str
    birthday: int
    phone: str
    verified: bool = False
    avatar: str = None
    email: str = None
