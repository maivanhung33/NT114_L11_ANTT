import os
import re
from datetime import datetime
from time import time

import bcrypt
from bson.code import Code
from django.http import JsonResponse
from rest_framework.decorators import api_view
from twilio.rest import Client

from get_media.model.user import TYPE_ADMIN, TYPE_USER
from get_media.module import auth
from get_media.module.database import DB
from get_media.request.user import UserLogin, UserRefresh
from get_media.service.log import write_log

ACCOUNT_SID = os.environ.get('ACCOUNT_SID') or 'ACcdb694e13e6682b8684c5c87b159e90e'
AUTH_TOKEN = os.environ.get('AUTH_TOKEN') or ''
SERVICE_ID = os.environ.get('SERVICE_ID') or 'VAbc7be24b5576704783b92dd68283da72'


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


@api_view(['GET'])
def list_user(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    limit = int(request.GET['limit']) if 'limit' in request.GET.keys() else 20
    offset = int(request.GET['offset']) if 'offset' in request.GET.keys() else 0
    q = request.GET['q'] if 'q' in request.GET.keys() else None

    query = {'type': TYPE_USER}
    optional_query = []
    if q is not None:
        rgx = re.compile('.*{}.*'.format(q), re.IGNORECASE)
        optional_query.append({'lastname': rgx})
        optional_query.append({'firstname': rgx})
        optional_query.append({'phone': rgx})
        query['$or'] = optional_query

    col = DB['user']
    count = col.find(query).count()
    users = list(col.find(query, {'_id': 0, 'password': 0}).limit(limit).skip(offset))

    return JsonResponse(status=200, data={'count': count, 'users': users})


@api_view(['GET'])
def list_collection(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    limit = int(request.GET['limit']) if 'limit' in request.GET.keys() else 20
    offset = int(request.GET['offset']) if 'offset' in request.GET.keys() else 0
    user = request.GET['user'] if 'user' in request.GET.keys() else None

    col = DB['collection']
    query = {}
    if user is not None:
        query['owner_phone'] = user
    count = col.find(query).count()
    collections = list(col.find(query).limit(limit).skip(offset))

    return JsonResponse(status=200, data={'count': count, 'collections': collections})


@api_view(['GET'])
def get_user(request, phone):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one({'type': TYPE_USER, 'phone': phone}, {'_id': 0, 'password': 0})
    if user is None:
        return JsonResponse(status=404, data={'message': 'User not found'})
    return JsonResponse(status=200, data=user)


@api_view(['POST'])
def deactivate_account(request, phone):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one({'type': TYPE_USER, 'phone': phone}, {'_id': 0, 'password': 0})
    if user is None:
        JsonResponse(status=404, data={'message': 'User not found'})
    if not user['is_active']:
        return JsonResponse(status=422, data={'message': 'Already disable'})

    user['is_active'] = False
    col.update_one({'type': TYPE_USER, 'phone': phone}, {'$set': user})
    write_log({}, 'deactivate_account', is_auth)

    return JsonResponse(status=200, data=user)


@api_view(['POST'])
def activate_account(request, phone):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    col = DB['user']
    user = col.find_one({'type': TYPE_USER, 'phone': phone}, {'_id': 0, 'password': 0})
    if user is None:
        return JsonResponse(status=404, data={'message': 'User not found'})
    if user['is_active']:
        return JsonResponse(status=422, data={'message': 'Already enable'})

    user['is_active'] = True
    col.update_one({'type': TYPE_USER, 'phone': phone}, {'$set': user})
    write_log({}, 'activate_account', is_auth)

    return JsonResponse(status=200, data=user)


@api_view(['GET'])
def list_logs(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    user = request.GET['user'] if 'user' in request.GET.keys() else None
    platform = request.GET['platform'] if 'platform' in request.GET.keys() else None
    log_type = request.GET['type'] if 'type' in request.GET.keys() else None
    limit = int(request.GET['limit']) if 'limit' in request.GET.keys() else 20
    offset = int(request.GET['offset']) if 'offset' in request.GET.keys() else 0
    start_from = int(request.GET['from']) if 'from' in request.GET.keys() else 0
    end_to = int(request.GET['to']) if 'to' in request.GET.keys() else 9999999999
    query = {'time': {'$gte': start_from, '$lte': end_to}}
    if log_type is not None:
        query['type'] = log_type
    if user is not None:
        query['user.phone'] = user
    if platform is not None:
        query['platform'] = platform

    col = DB['log']
    count = col.find(query, {'_id': 0}).count()
    logs = list(col.find(query, {'_id': 0}).limit(limit).skip(offset).sort('time', -1))
    return JsonResponse(status=200, data={'count': count, 'logs': logs})


@api_view(['GET'])
def get_statistics(request):
    is_auth = check_token(request)
    if isinstance(is_auth, JsonResponse):
        return is_auth

    statistic_type = request.GET['type'] if 'type' in request.GET.keys() else 'platform'
    end_to = int(request.GET['to']) if 'to' in request.GET.keys() else int(datetime.now().timestamp())
    start_from = int(request.GET['from']) if 'from' in request.GET.keys() else end_to - 2592000

    response = {'data': []}
    col = DB['log']
    if statistic_type == 'platform':
        map = Code('function() { emit(this.platform,1); }')
        reduce = Code('function(key, values) {return Array.sum(values)}')
        x = col.map_reduce(map, reduce, "statistic_platform",
                           query={"type": "crawl", "time": {"$gt": start_from, "$lte": end_to}})
        for doc in x.find().sort('value', -1):
            if doc['_id'] is None:
                continue
            response['data'].append({'platform': doc['_id'], 'count': int(doc['value'])})
        DB['statistic_platform'].drop()
    elif statistic_type == 'link':
        map = Code('function() { emit(this.url,1); }')
        reduce = Code('function(key, values) {return Array.sum(values)}')
        x = col.map_reduce(map, reduce, "statistic_link",
                           query={"type": "crawl", "time": {"$gt": start_from, "$lte": end_to}})
        for doc in x.find().sort('value', -1):
            if doc['_id'] is None:
                continue
            response['data'].append({'link': doc['_id'], 'count': int(doc['value'])})
        DB['statistic_link'].drop()
    elif statistic_type == 'user':
        map = Code('function() { emit(this.user,1); }')
        reduce = Code('function(key, values) {return Array.sum(values)}')
        x = col.map_reduce(map, reduce, "statistic_user",
                           query={"type": "crawl", "time": {"$gt": start_from, "$lte": end_to}})
        for doc in x.find().sort('value', -1):
            if doc['_id'] is None:
                continue
            response['data'].append({'user': doc['_id'], 'count': int(doc['value'])})
        DB['statistic_user'].drop()
    elif statistic_type == 'item':
        map = Code('function() { emit(this.source,1); }')
        reduce = Code('function(key, values) {return Array.sum(values)}')
        x = col.map_reduce(map, reduce, "statistic_item",
                           query={"type": "add_item", "time": {"$gt": start_from, "$lte": end_to}})
        for doc in x.find().sort('value', -1):
            if doc['_id'] is None:
                continue
            response['data'].append({'link': doc['_id'], 'count': int(doc['value'])})
        DB['statistic_item'].drop()
    elif statistic_type == 'register':
        query = {'type': 'register', 'time': {'$gte': start_from, '$lte': end_to}}
        count = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'register', 'count': count})
        query = {'type': 'register_success', 'time': {'$gte': start_from, '$lte': end_to}}
        count = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'registerSuccess', 'count': count})
    elif statistic_type == 'crawl':
        query = {'type': 'crawl', 'time': {'$gte': start_from, '$lte': end_to}}
        count_total = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'total', 'count': count_total})
        query = {'type': 'crawl', 'time': {'$gte': start_from, '$lte': end_to}, 'user': None}
        count_anonymous = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'anonymous', 'count': count_anonymous})
        response['data'].append({'type': 'user', 'count': count_total - count_anonymous})
    elif statistic_type == 'collection':
        query = {'type': 'create_collection', 'time': {'$gte': start_from, '$lte': end_to}}
        count_total = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'create', 'count': count_total})
        query = {'type': 'remove_collection', 'time': {'$gte': start_from, '$lte': end_to}}
        count_total = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'remove', 'count': count_total})
        query = {'type': 'add_item', 'time': {'$gte': start_from, '$lte': end_to}}
        count_total = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'addItem', 'count': count_total})
        query = {'type': 'remove_item', 'time': {'$gte': start_from, '$lte': end_to}}
        count_total = col.find(query, {'_id'}).count()
        response['data'].append({'type': 'removeItem', 'count': count_total})
    return JsonResponse(status=200, data=response)


def login(data):
    if not validation_phone(data.cleaned_data['phone']):
        return JsonResponse(status=400, data=dict(message='Wrong phone number format'))
    col = DB['user']
    user = col.find_one({'phone': data.cleaned_data['phone'], 'verified': True, 'type': TYPE_ADMIN})
    if not user:
        return JsonResponse(status=404, data=dict(message='User not exits'))
    if not bcrypt.checkpw(data.cleaned_data['password'].encode(), user['password'].encode()):
        return JsonResponse(status=401, data=dict(message='Password is not correct'))
    if not user['is_active']:
        return JsonResponse(status=401, data=dict(message='Account has been disable'))

    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
                                                           firstname=user['firstname'],
                                                           lastname=user['lastname'],
                                                           email=user['email'],
                                                           type=TYPE_ADMIN).decode(),
                    refreshToken=auth.generate_refresh_token(phone=user['phone'],
                                                             email=user['email'],
                                                             password=user['password'],
                                                             type=TYPE_ADMIN).decode(),
                    expireAt=int(time()) + 3600)
    write_log({}, 'admin_login', {'phone': user['phone']})
    return JsonResponse(status=200, data=response)


def refresh(data):
    user = auth.check_refresh_token(data.cleaned_data['refresh_token'])
    if user in [0, -1]:
        return JsonResponse(status=400, data={'message': 'Refresh token is not correct or expired'})
    col = DB['user']
    user = col.find_one({'password': user.password, 'phone': user.phone, 'is_active': True, 'type': TYPE_ADMIN})
    if not user:
        return JsonResponse(status=400, data={'message': 'Can not refresh token'})
    response = dict(accessToken=auth.generate_access_token(phone=user['phone'],
                                                           firstname=user['firstname'],
                                                           lastname=user['lastname'],
                                                           email=user['email'],
                                                           type=TYPE_ADMIN).decode(),
                    refreshToken=data.cleaned_data['refresh_token'],
                    expireAt=int(time()) + 3600)
    return JsonResponse(status=200, data=response)


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
    elif is_auth.type != TYPE_ADMIN:
        return JsonResponse(status=401, data={'message': 'Unauthenticated'})
    return is_auth
