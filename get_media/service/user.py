import json
import os
import re
from datetime import datetime
from time import time

import bcrypt
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from rest_framework.decorators import api_view
from twilio.rest import Client

from get_media.model.user import User
from get_media.module import auth
from get_media.module.database import database
from get_media.request.user import UserRegister, UserLogin, UserRefresh, VerifyOtpRegister, ResetPassword, \
    VerifyOtpResetPassword, AvatarUpload, UserUpdate

DB = database()

ACCOUNT_SID = os.environ.get('ACCOUNT_SID') or 'ACcdb694e13e6682b8684c5c87b159e90e'
AUTH_TOKEN = os.environ.get('AUTH_TOKEN') or ''
SERVICE_ID = os.environ.get('SERVICE_ID') or 'VAbc7be24b5576704783b92dd68283da72'


@api_view(['POST'])
def register(request):
    form = UserRegister(request.POST)
    validate_form = validate_phone_request_form(form)
    if validate_form is not None:
        return validate_form

    col = DB['user']
    is_exits = col.find_one({'phone': form.cleaned_data['phone'], 'verified': True})
    if is_exits:
        return JsonResponse(status=422, data=dict(message='User name has exits'))
    new_user = User(phone=form.cleaned_data['phone'],
                    password=bcrypt.hashpw(form.cleaned_data['password'].encode(), bcrypt.gensalt()).decode(),
                    lastname=form.cleaned_data['lastname'],
                    firstname=form.cleaned_data['firstname'],
                    birthday=form.cleaned_data['birthday'],
                    favorites=[])

    col.update({'phone': form.cleaned_data['phone']}, {'$set': new_user.__dict__}, upsert=True)

    send_otp(form.cleaned_data['phone'])

    return JsonResponse(status=201,
                        data={'status': 'success', 'message': 'Waiting for verifying your phone'})


@api_view(['POST'])
def token(request):
    form = UserLogin(request.POST)
    if form.is_valid():
        if form.cleaned_data['grant_type'] != 'password':
            return JsonResponse(status=400, data=dict(message='Grant type is not valid'))
        return login(form)
    else:
        form = UserRefresh(request.POST)
        if not form.is_valid():
            return JsonResponse(status=400, data=dict(message='Bad Request'))
        if form.cleaned_data['grant_type'] != 'refresh_token':
            return JsonResponse(status=400, data=dict(message='Grant type is not valid'))
        return refresh(form)


@api_view(['POST'])
def reset_password(request):
    form = ResetPassword(request.POST)
    validate_form = validate_phone_request_form(form)
    if validate_form is not None:
        return validate_form

    col = DB['user']
    user = col.find_one({'phone': form.cleaned_data['phone'], 'verified': True})
    if not user:
        return JsonResponse(status=404, data=dict(message='User not exits'))

    send_otp(form.cleaned_data['phone'])

    return JsonResponse(status=200, data={'status': 'pending', 'message': 'waiting confirm otp'})


@api_view(['POST'])
def verify_opt_register(request):
    form = VerifyOtpRegister(request.POST)
    validate_form = validate_phone_request_form(form)
    if validate_form is not None:
        return validate_form

    col = DB['user']
    user = col.find_one({'phone': form.cleaned_data['phone'], 'verified': False})
    if not user:
        return JsonResponse(status=404, data=dict(message='User not exits or Has verified'))

    if verify_otp(phone=form.cleaned_data['phone'], otp=form.cleaned_data['otp']) == 'approved':
        update_verified = {'$set': {'verified': True}}
        col.update_one({'phone': form.cleaned_data['phone']}, update_verified)
        return JsonResponse(status=200, data={'status': 'success', 'message': 'Verified'})
    return JsonResponse(status=404, data={'status': 'fail', 'message': 'Otp incorrect'})


@api_view(['POST'])
def verify_opt_reset_password(request):
    form = VerifyOtpResetPassword(request.POST)
    validate_form = validate_phone_request_form(form)
    if validate_form is not None:
        return validate_form

    col = DB['user']
    user = col.find_one({'phone': form.cleaned_data['phone'], 'verified': True})
    if not user:
        return JsonResponse(status=404, data=dict(message='User not exits'))

    if verify_otp(phone=form.cleaned_data['phone'], otp=form.cleaned_data['otp']) == 'approved':
        update_password = {
            '$set': {'password': bcrypt.hashpw(form.cleaned_data['password'].encode(), bcrypt.gensalt()).decode()}}
        col.update_one({'phone': form.cleaned_data['phone']}, update_password)
        return JsonResponse(status=200, data={'status': 'success', 'message': 'Password has been updated'})
    return JsonResponse(status=404, data={'status': 'fail', 'message': 'Otp incorrect'})


@api_view(['GET'])
def get_user(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one(
        {'phone': is_auth.phone, 'verified': True},
        {'_id': 0, 'password': 0, 'favorites': 0})

    return JsonResponse(status=200, data=user)


@api_view(['PUT'])
def update_user(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    form = UserUpdate(request.POST)
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message='Bad Request'))

    data = {'birthday': form.cleaned_data['birthday'],
            'firstname': form.cleaned_data['firstname'],
            'lastname': form.cleaned_data['lastname'],
            'email': form.cleaned_data['email']}
    col = DB['user']
    col.update_one({'phone': is_auth.phone, 'verified': True}, {'$set': data})

    return JsonResponse(status=200, data={'message': 'success'})


@api_view(['GET', 'POST'])
def avatar(request):
    if request.method == 'GET':
        return get_avatar(request)
    elif request.method == 'POST':
        return upload_avatar(request)


@api_view(['POST'])
def add_to_collection(request):
    try:
        request_data: dict = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse(data={'message': 'BAD_REQUEST'}, status=400)
    if 'url' not in request_data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    if 'thumbnail' not in request_data.keys():
        return JsonResponse(data={'message': 'THUMBNAIL_REQUIRED'}, status=400)
    if 'type' not in request_data.keys():
        return JsonResponse(data={'message': 'TYPE_REQUIRED'}, status=400)
    if 'platform' not in request_data.keys():
        return JsonResponse(data={'message': 'PLATFORM_REQUIRED'}, status=400)
    if 'source' not in request_data.keys():
        return JsonResponse(data={'message': 'SOURCE_REQUIRED'}, status=400)
    if 'id' not in request_data.keys():
        return JsonResponse(data={'message': 'ID_REQUIRED'}, status=400)

    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    update_data = dict(
        id=request_data['id'],
        url=request_data['url'],
        type=request_data['type'],
        thumbnail=request_data['thumbnail'],
        platform=request_data['platform'],
        source=request_data['source']
    )
    collection = get_user_collection(is_auth)
    if check_added(collection, request_data['id'], request_data['platform']):
        return JsonResponse(status=422, data={'message': 'Already exist'})
    col.update_one({'phone': is_auth.phone, 'verified': True}, {'$push': {'favorites': update_data}})
    write_log_collection(update_data, is_auth)
    return JsonResponse(status=200, data={'message': 'Success'})


@api_view(['POST'])
def remove_from_collection(request):
    try:
        request_data: dict = json.loads(request.body.decode('utf-8'))
    except:
        return JsonResponse(data={'message': 'BAD_REQUEST'}, status=400)

    if 'id' not in request_data.keys():
        return JsonResponse(data={'message': 'ID_REQUIRED'}, status=400)

    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    collection = get_user_collection(is_auth)
    clone_col = []
    for item in collection:
        if item['id'] == request_data['id']:
            continue
        clone_col.append(item)

    col.update_one({'phone': is_auth.phone, 'verified': True}, {'$set': {'favorites': clone_col}})
    return JsonResponse(status=200, data={'message': 'Success'})


@api_view(['GET'])
def get_collection(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one({'phone': is_auth.phone, 'verified': True}, {'favorites': 1})

    return JsonResponse(status=200, data={'count': len(user['favorites']), 'favorites': user['favorites']})


def get_avatar(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one({'phone': is_auth.phone, 'verified': True}, {'avatar': 1})

    try:
        file_location = 'get_media/images{}'.format(user['avatar'])
        image_data = open(file_location, "rb").read()
        content_type = 'image/' + user['avatar'].split('.')[1]
        return HttpResponse(image_data, content_type=content_type)
    except IOError:
        return HttpResponseNotFound('Not Found')


def upload_avatar(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    form = AvatarUpload(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message='Bad Request'))

    avatar_type = form.cleaned_data['avatar'].content_type
    if avatar_type not in ['image/jpeg', 'image/png']:
        return JsonResponse(status=400, data=dict(message='Avatar must be JPEG or PNG'))
    avatar_extension = avatar_type.split('/')[1]

    avatar_url = handle_uploaded_file(form.cleaned_data['avatar'], is_auth.phone, avatar_extension)

    col = DB['user']
    col.update_one({'phone': is_auth.phone}, {'$set': {'avatar': avatar_url}})

    return JsonResponse(status=200, data={'url': avatar_url})


def login(data):
    if not validation_phone(data.cleaned_data['phone']):
        return JsonResponse(status=400, data=dict(message='Wrong phone number format'))
    col = DB['user']
    user = col.find_one({'phone': data.cleaned_data['phone'], 'verified': True})
    if not user:
        return JsonResponse(status=404, data=dict(message='User not exits'))
    if not bcrypt.checkpw(data.cleaned_data['password'].encode(), user['password'].encode()):
        return JsonResponse(status=401, data=dict(message='Password is not correct'))

    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
                                                           firstname=user['firstname'],
                                                           lastname=user['lastname'],
                                                           email=user['email']).decode(),
                    refreshToken=auth.generate_refresh_token(phone=user['phone'],
                                                             email=user['email'],
                                                             password=user['password']).decode(),
                    expireAt=int(time()) + 3600)
    return JsonResponse(status=200,
                        data=response)


def refresh(data):
    user = auth.check_refresh_token(data.cleaned_data['refresh_token'])
    if user in [0, -1]:
        return JsonResponse(status=400, data={'message': 'Refresh token is not correct or expired'})
    col = DB['user']
    user = col.find_one({'password': user.password})
    if not user:
        return JsonResponse(status=400, data={'message': 'Can not refresh token'})
    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
                                                           firstname=user['firstname'],
                                                           lastname=user['lastname'],
                                                           email=user['email']).decode(),
                    refreshToken=data.cleaned_data['refresh_token'],
                    expireAt=int(time()) + 3600)
    return JsonResponse(status=200,
                        data=response)


def handle_uploaded_file(f, phone, extension):
    fs = FileSystemStorage(location='get_media/images')
    fs.delete('{}.{}'.format(phone, extension))
    filename = fs.save('{}.{}'.format(phone, extension), f)
    return fs.url(filename)


def send_otp(phone):
    phone = phone.lstrip('0')
    phone_send_otp = '+84' + phone
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    return client.verify \
        .services(SERVICE_ID) \
        .verifications \
        .create(to=phone_send_otp, channel='sms')


def verify_otp(phone, otp):
    phone = phone.lstrip('0')
    phone_send_otp = '+84' + phone
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    verification_check = client.verify \
        .services(SERVICE_ID) \
        .verification_checks \
        .create(to=phone_send_otp, code=otp)
    return verification_check.status


def validation_phone(input_string):
    regex = re.compile('^(0)[1-9][0-9]{8}$', re.I)
    match = regex.match(str(input_string))
    return bool(match)


def validate_phone_request_form(form):
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message='Bad Request'))
    if not validation_phone(form.cleaned_data['phone']):
        return JsonResponse(status=400, data=dict(message='Wrong phone number format'))


def check_token(request):
    try:
        access_token = request.headers['Authorization'].split(' ')[1]
    except:
        return JsonResponse(status=401, data={'message': 'Unauthenticated'})
    is_auth = auth.check_access_token(access_token)
    if is_auth == -1:
        return JsonResponse(status=401, data={'message': 'Unauthenticated'})
    elif is_auth == 0:
        return JsonResponse(status=401, data={'message': 'Token invalid'})
    return is_auth


def write_log_collection(data, user=None):
    col = DB['log']
    data['time'] = datetime.now()
    data['type'] = 'collection'
    data['user'] = user.__dict__ if user is not None else None
    col.insert_one(data)


def get_user_collection(is_auth):
    col = DB['user']
    user = col.find_one({'phone': is_auth.phone, 'verified': True}, {'favorites': 1})
    return user['favorites']


def check_added(collection, id, platform):
    for item in collection:
        if item['id'] == id and item['platform'] == platform:
            return True
    return False
