import json
from datetime import datetime

import requests
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view

from get_media.model.user import TYPE_USER
from get_media.module import auth
from get_media.module.database import DB
from get_media.module.facebook import FaceBook
from get_media.module.instagram import InstaAPI
from get_media.module.tiktok import TikTok
from get_media.service.log import write_log

TYPE_HIGHLIGHT = 'highlight'
TYPE_CRAWL = 'crawl'


@api_view(['POST'])
def get_video_facebook(request):
    is_auth = check_token(request)
    # Validate request
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    limit = data['limit'] if 'limit' in data.keys() else 10
    cursor = data['cursor'] if 'cursor' in data.keys() else None

    request_type = data['requestType'] if 'requestType' in data.keys() else TYPE_CRAWL
    if request_type == TYPE_CRAWL:
        write_log({'url': data['url'], 'platform': 'facebook'}, 'crawl', is_auth)
    # Check existence
    facebook = FaceBook(data['url'])
    is_existing = find_existence(facebook.get_url(), limit, cursor)
    if is_existing is not None:
        is_existing = check_added(is_auth, is_existing, 'facebook')
        return JsonResponse(status=200, data=is_existing)

    # Crawl
    response = facebook.crawl(limit, cursor)
    if response is None:
        return JsonResponse(status=200, data={'owner': None, 'data': None, 'hasNextPage': False, 'cursor': None})
    response = check_added(is_auth, response, 'facebook')
    response['srcUrl'] = facebook.get_url()
    write_data(response, limit, cursor)
    return JsonResponse(status=200, data=response)


@api_view(['GET'])
def get_video_tiktok(request):
    # Validate request
    if 'url' not in request.GET.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    # Crawl
    try:
        tiktok = TikTok(request.GET['url'])
        data = tiktok.get_link()
        response = requests.get(data['url'], headers=data['headers'])
        return HttpResponse(response.content, content_type='video/mp4')
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data=dict(url=None, headers=None, user=None))


@api_view(['GET'])
def get_video_tiktok_info(request):
    is_auth = check_token(request)
    if 'url' not in request.GET.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        write_log({'url': request.GET['url'], 'platform': 'tiktok'}, 'crawl', is_auth)
        tiktok = TikTok(request.GET['url'])
        data = tiktok.get_link()
        check_added(is_auth, data, 'tiktok')
        return JsonResponse(status=200, data=data)
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data=dict(url=None, headers=None, user=None))


@api_view(['POST'])
def get_insta_media(request):
    is_auth = check_token(request)

    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    limit = data['limit'] if 'limit' in data.keys() else 50
    cursor = data['cursor'] if 'cursor' in data.keys() else ''

    request_type = data['requestType'] if 'requestType' in data.keys() else TYPE_CRAWL
    if request_type == TYPE_CRAWL:
        write_log({'url': data['url'], 'platform': 'instagram'}, 'crawl', is_auth)

    insta = InstaAPI(data['url'])
    is_existing = find_existence(insta.get_url(), limit, cursor)
    if is_existing is not None:
        is_existing = check_added(is_auth, is_existing, 'instagram')
        return JsonResponse(status=200, data=is_existing)

    info = insta.crawl(limit, cursor)
    if info is None:
        return JsonResponse(status=200, data=dict(owner=None, data=None))
    owner = {}
    if info['user'] is not None:
        owner: dict = {
            "avatar": info['user']['profile_pic_url'],
            "username": info['user']['username'],
            "fullname": info['user']['full_name'],
            "countPost": info['user']['edge_owner_to_timeline_media']['count'],
            "countFollowedBy": info['user']['edge_followed_by']['count']
        }
    elif info['user'] is None:
        owner: dict = {
            "avatar": info['data'][0]['owner']['profile_pic_url'],
            "username": info['data'][0]['owner']['username'],
            "fullname": info['data'][0]['owner']['full_name'],
            "countPost": info['data'][0]['owner']['edge_owner_to_timeline_media']['count'],
            "countFollowedBy": None
        }
    posts: list = []
    for i in info['data']:
        url = None
        if i['is_video'] is True:
            url = i['video_url']
        elif i['is_video'] is False:
            url = i['display_url']
        post: dict = {
            "id": i['shortcode'] if i['shortcode'] is not None else None,
            "source": 'https://www.instagram.com/p/{}/'.format(i['shortcode']) if i['shortcode'] is not None else None,
            "url": url,
            'thumbnail': i['display_url'],
            "isVideo": i['is_video'],
            "width": i['dimensions']['width'] if i['dimensions']['width'] is not None else None,
            "height": i['dimensions']['height'] if i['dimensions']['height'] is not None else None,
            "countComment": i['edge_media_to_comment']['count'],
            "countLike": i['edge_media_preview_like']['count']
        }
        posts.append(post)

    response = dict(cursor=info['cursor'], hasNextPage=info['has_next_page'], owner=owner, data=posts,
                    srcUrl=insta.get_url())
    write_data(response, limit, cursor)
    response = check_added(is_auth, response, 'instagram')

    return JsonResponse(status=200, data=response)


def find_existence(link, limit, cursor=None):
    col = DB['media']
    if cursor is None:
        query = {'srcUrl': link, 'limit': limit, }
    else:
        query = {'srcUrl': link, 'limit': limit, 'first': cursor}
    is_exit = col.find_one(query, {'_id': 0, 'first': 0, 'limit': 0, '_expireAt': 0})
    if is_exit is not None:
        return is_exit
    return None


def write_data(data, limit, first=None):
    col = DB['media']
    data['_expireAt'] = datetime.now()
    data['limit'] = limit
    data['first'] = first
    col.insert_one(data)

    del data['_id']
    del data['_expireAt']
    del data['limit']
    del data['first']


def check_token(request):
    try:
        access_token = request.headers['Authorization'].split(' ')[1]
        is_auth = auth.check_access_token(access_token)
        if is_auth == -1 or is_auth == 0 or is_auth.type != TYPE_USER:
            return
        return is_auth
    except:
        return


def get_user_collection(is_auth):
    col = DB['user']
    user = col.find_one({'phone': is_auth.phone, 'verified': True}, {'favorites': 1})

    return user['favorites']


def check_added(is_auth, response, platform):
    col = DB['collection_item']
    user_items = list(col.find({'owner_phone': is_auth.phone}, {'collection_id': 1, 'id': 1}))
    if platform == 'tiktok':
        if is_auth is None:
            response['isAdded'] = False
            response['collectionId'] = None
            return response
        response['isAdded'] = False
        response['collectionId'] = []
        for item in user_items:
            if item['id'] != response['id']:
                continue
            response['isAdded'] = True
            response['collectionId'].append(item['collection_id'])
        return response
    else:
        if is_auth is None:
            for response_item in response['data']:
                response_item['isAdded'] = False
                response_item['collectionId'] = None
            return response
        for response_item in response['data']:
            response_item['isAdded'] = False
            response_item['collectionId'] = []
            for user_item in user_items:
                if user_item['id'] != response_item['id']:
                    continue
                response_item['isAdded'] = True
                response_item['collectionId'].append(user_item['collection_id'])
        return response
