import hashlib
import json
import os
import time

import jwt
from django.http import JsonResponse

import get_media.response.user as user_response
from get_media.model.user import User
from get_media.module.database import database
from get_media.response.error import BAD_REQUEST, METHOD_NOT_ALLOW, ALL_READY_EXITS, NOT_ENOUGH_INFO, LOGIN_FAIL, \
    TOKEN_EXPIRED, MUST_LOGIN

db = database()
COL_USER = os.environ.get('COL_USER') or 'insta_down_data_user'
SECRET = 'nhomt@m-nt208.k21.antt'
TOKEN_EXPIRE = os.environ.get('TOKEN_USER') or 3600


def register(request):
    if request.method != 'POST':
        return METHOD_NOT_ALLOW

    try:
        body: dict = json.loads(request.body.decode('utf-8'))
        if 'username' not in body.keys() \
                or 'password' not in body.keys() \
                or 'birthday' not in body.keys() \
                or 'email' not in body.keys() \
                or 'phone' not in body.keys() \
                or 'fullname' not in body.keys():
            return NOT_ENOUGH_INFO
    except Exception as e:
        print(e)
        return NOT_ENOUGH_INFO

    # Check if username exist
    is_exits = db[COL_USER].find_one({'username': body['username']}, {'_id': 1})
    if is_exits is not None:  # Exist
        return ALL_READY_EXITS
    # Not exist -> create new user.
    new_user = User(
        username=body['username'],
        password=hashlib.sha256(body['password'].encode('utf-8')).hexdigest(),
        fullname=body['fullname'],
        birthday=body['birthday'],
        phone=body['phone'],
        email=body['email'],
        insta_like=[]
    )
    db[COL_USER].insert(new_user.__dict__)
    return JsonResponse(data=user_response.to_dict(new_user), status=200)


def login(request):
    if request.method != 'POST':
        return METHOD_NOT_ALLOW

    try:
        body: dict = json.loads(request.body.decode('utf-8'))
        if 'username' not in body.keys() or 'password' not in body.keys():
            return BAD_REQUEST
    except Exception as e:
        print(e)
        return BAD_REQUEST

    # login
    username = body['username']
    password = hashlib.sha256(body['password'].encode('utf-8')).hexdigest()
    logging_user = db[COL_USER].find_one({'username': username, 'password': password}, {'_id': 1})
    if logging_user is None:
        return LOGIN_FAIL

    # Login successful, generate JWT
    now = int(time.time())
    token_expire_at = now + 3600
    data = {
        "username": username,
        "start_at": now,
        "exp": token_expire_at
    }
    token = jwt.encode(data, SECRET, algorithm='HS256')

    return JsonResponse(data={"message": 'Login successful.', "token": token.decode(), "expireAt": token_expire_at},
                        status=200)


def info(request):
    if request.method != 'GET':
        return METHOD_NOT_ALLOW

    # Get token
    try:
        token = request.headers['Authorization'].split(' ')[1]
    except Exception as e:
        print(e)
        return MUST_LOGIN

    # Check token
    try:
        data = jwt.decode(jwt=token, key=SECRET, algorithm='HS256')
    except jwt.ExpiredSignatureError:
        return TOKEN_EXPIRED

    # get info user
    username = data['username']
    user = db[COL_USER].find_one({'username': username}, {'_id': 0})
    user = User(
        username=user['username'],
        password=user['password'],
        fullname=user['fullname'],
        birthday=user['birthday'],
        phone=user['phone'],
        email=user['email'],
        insta_like=user['insta_like']
    )
    return JsonResponse(data=user_response.to_dict(user), status=200)
