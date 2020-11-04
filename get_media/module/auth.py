import os
import time
from dataclasses import dataclass

import bcrypt as bcrypt
import jwt

SECRET = os.environ.get('SECRET') or 'uit.edu.vn'


@dataclass
class RefreshTokenInfo:
    phone: str
    password: bcrypt
    email: str = None

    @staticmethod
    def new(data: dict):
        return RefreshTokenInfo(phone=data['phone'], password=data['password'], email=data['email'])


def generate_access_token(phone, email):
    now = int(time.time())
    token_expire_at = now + 3600
    data = {
        "phone": phone,
        "email": email,
        "start_at": now,
        "exp": token_expire_at,
    }
    return jwt.encode(data, SECRET, algorithm='HS256')


def generate_refresh_token(phone, email, password):
    data = {
        "phone": phone,
        "email": email,
        "password": password
    }
    return jwt.encode(data, SECRET, algorithm='HS256')


def check_refresh_token(token):
    try:
        data = jwt.decode(jwt=token, key=SECRET, algorithm='HS256')
        return RefreshTokenInfo.new(data)
    except jwt.ExpiredSignatureError:
        return 0
    except jwt.InvalidTokenError:
        return -1
