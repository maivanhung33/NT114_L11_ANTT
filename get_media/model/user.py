from dataclasses import dataclass

TYPE_ADMIN = 'admin'
TYPE_USER = 'user'


@dataclass
class User:
    password: str
    lastname: str
    firstname: str
    birthday: int
    phone: str
    type: str = TYPE_USER
    is_active: bool = True
    verified: bool = False
    avatar: str = None
    email: str = None
