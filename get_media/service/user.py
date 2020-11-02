from time import time

import bcrypt
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from rest_framework.decorators import api_view

from get_media.model.user import User
from get_media.module import auth
from get_media.module.database import database
from get_media.request.user import UserRegister, UserLogin, UserRefresh

DB = database()


@api_view(['POST'])
def register(request):
    form = UserRegister(request.POST)
    if not form.is_valid():
        return JsonResponse(status=400, data=dict(message="Bad Request"))

    col = DB["user"]
    is_exits = col.find_one({"username": form.cleaned_data['username']})
    if is_exits:
        return JsonResponse(status=422, data=dict(message="User name has exits"))
    new_user = User(username=form.cleaned_data['username'],
                    password=bcrypt.hashpw(form.cleaned_data['password'].encode(), bcrypt.gensalt()).decode(),
                    lastname=form.cleaned_data['lastname'],
                    firstname=form.cleaned_data['firstname'],
                    birthday=form.cleaned_data['birthday'],
                    favorites=[])
    col.insert_one(new_user.__dict__)
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
    user = col.find_one({"username": data.cleaned_data['username']})
    if not user:
        return JsonResponse(status=404, data=dict(message="User not exits"))
    if not bcrypt.checkpw(data.cleaned_data['password'].encode(), user['password'].encode()):
        return JsonResponse(status=401, data=dict(message="Password is not correct"))

    response = dict(accessToken=auth.generate_access_token(username=user['username'],
                                                           email=user['email']).decode(),
                    refreshToken=auth.generate_refresh_token(username=user['username'],
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
    response = dict(accessToken=auth.generate_access_token(username=user['username'],
                                                           email=user['email']).decode(),
                    refreshToken=data.cleaned_data['refresh_token'],
                    expireAt=int(time()) + 3600)
    return JsonResponse(status=200,
                        data=response)


def handle_uploaded_file(f, username, extension):
    fs = FileSystemStorage(location='get_media/images')
    filename = fs.save('{}.{}'.format(username, extension), f)
    return fs.url(filename)

# def update():
#     avatar_type = form.cleaned_data["avatar"].content_type
#     if avatar_type not in ['image/jpeg', 'image/png']:
#         return JsonResponse(status=400, data=dict(message="Avatar must be JPEG or PNG"))
#     avatar_extension = avatar_type.split('/')[1]
#     avatar_url = handle_uploaded_file(form.cleaned_data['avatar'], form.cleaned_data['username'], avatar_extension)
