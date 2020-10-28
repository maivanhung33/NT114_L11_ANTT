import os
import time
from dataclasses import dataclass

import bcrypt as bcrypt
import jwt

SECRET = os.environ.get('SECRET') or 'uit.edu.vn'


@dataclass
class TokenInfo:
    username: str
    password: bcrypt
    email: str = None

    @staticmethod
    def new(data: dict):
        return TokenInfo(username=data['username'])


def generate_access_token(username, email):
    now = int(time.time())
    token_expire_at = now + 3600
    data = {
        "username": username,
        "email": email,
        "start_at": now,
        "exp": token_expire_at,
    }
    return jwt.encode(data, SECRET, algorithm='HS256')


def generate_refresh_token(username, email, password):
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    return jwt.encode(data, SECRET, algorithm='HS256')


def check_token(request):
    try:
        token = request.headers['Authorization'].split(' ')[1]
    except Exception as e:
        raise e

    try:
        data = jwt.decode(jwt=token, key=SECRET, algorithm='HS256')
        return TokenInfo.new(data)
    except jwt.ExpiredSignatureError:
        return 0
    except jwt.InvalidTokenError:
        return -1
