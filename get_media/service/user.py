from time import time

import bcrypt
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework.decorators import api_view
import os
from get_media.model.user import User
from get_media.module import auth
from get_media.module.database import database
from get_media.request.user import UserRegister, UserLogin, UserRefresh, UserConfirmOtp
from twilio.rest import Client

DB = database()


@api_view(['POST'])
def register(request):
    form = UserRegister(request.POST)
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message="Bad Request"))

    col = DB["user"]
    is_exits = col.find_one({"phone": form.cleaned_data['phone']})
    if is_exits:
        return JsonResponse(status=422, data=dict(message="User name has exits"))
    new_user = User(phone=form.cleaned_data['phone'],
                    password=bcrypt.hashpw(form.cleaned_data['password'].encode(), bcrypt.gensalt()).decode(),
                    lastname=form.cleaned_data['lastname'],
                    firstname=form.cleaned_data['firstname'],
                    birthday=form.cleaned_data['birthday'],
                    favorites=[])
    col.insert_one(new_user.__dict__)
    phone_send_otp = form.cleaned_data['phone'].replace("0", "+84")

    account_sid = 'ACcdb694e13e6682b8684c5c87b159e90e'
    auth_token = '4f22963775df5caa493fd39486236ff0'
    service_id = 'VAbc7be24b5576704783b92dd68283da72'

    client = Client(account_sid, auth_token)

    verification = client.verify \
        .services(service_id) \
        .verifications \
        .create(to=phone_send_otp, channel='sms')
    return JsonResponse(status=201,
                        data={"status": "success", "message": ""})


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
            return JsonResponse(status=400, data=dict(message="Bad Request"))
        if form.cleaned_data['grant_type'] != 'refresh_token':
            return JsonResponse(status=400, data=dict(message='Grant type is not valid'))
        return refresh(form)


def login(data):
    col = DB["user"]
    user = col.find_one({"phone": data.cleaned_data['phone']})
    if not user:
        return JsonResponse(status=404, data=dict(message="User not exits"))
    if not bcrypt.checkpw(data.cleaned_data['password'].encode(), user['password'].encode()):
        return JsonResponse(status=401, data=dict(message="Password is not correct"))

    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
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
    col = DB["user"]
    user = col.find_one({"password": user.password})
    if not user:
        return JsonResponse(status=400, data={'message': 'Can not refresh token'})
    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
                                                           email=user['email']).decode(),
                    refreshToken=data.cleaned_data['refresh_token'],
                    expireAt=int(time()) + 3600)
    return JsonResponse(status=200,
                        data=response)


def handle_uploaded_file(f, username, extension):
    fs = FileSystemStorage(location='get_media/images')
    filename = fs.save('{}.{}'.format(username, extension), f)
    return fs.url(filename)


@api_view(['POST'])
def confirm_otp(request):
    form = UserConfirmOtp(request.POST)
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message="Bad Request"))

    col = DB["user"]
    user = col.find_one({"phone": form.cleaned_data['phone']})
    if not user:
        return JsonResponse(status=404, data=dict(message="User not exits"))

    phone_send_otp = form.cleaned_data['phone'].replace("0", "+84")
    account_sid = 'ACcdb694e13e6682b8684c5c87b159e90e'
    auth_token = '4f22963775df5caa493fd39486236ff0'
    service_id = 'VAbc7be24b5576704783b92dd68283da72'

    client = Client(account_sid, auth_token)
    verification_check = client.verify \
        .services(service_id) \
        .verification_checks \
        .create(to=phone_send_otp, code=form.cleaned_data['otp'])
    if verification_check.status == 'approved':
        update_verified = {"$set": {"verified": True}}
        col.update_one({"phone": form.cleaned_data['phone']}, update_verified)
        return JsonResponse(status=200, data={"status": "success", "message": ""})
    return JsonResponse(status=404, data={"status": "fail", "message": "Otp incorrect"})


# def update():
#     avatar_type = form.cleaned_data["avatar"].content_type
#     if avatar_type not in ['image/jpeg', 'image/png']:
#         return JsonResponse(status=400, data=dict(message="Avatar must be JPEG or PNG"))
#     avatar_extension = avatar_type.split('/')[1]
#     avatar_url = handle_uploaded_file(form.cleaned_data['avatar'], form.cleaned_data['username'], avatar_extension)
