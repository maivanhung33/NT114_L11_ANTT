import json
from datetime import datetime

import requests
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view

from get_media.module.database import database
from get_media.module.facebook import FaceBook
from get_media.module.instagram import InstaAPI
from get_media.module.tiktok import TikTok

DB = database()


@api_view(['POST'])
def get_video_facebook(request):
    # Validate request
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)

    # Check existence
    facebook = FaceBook(data['url'])
    is_existing = find_existence(facebook.get_url())
    if is_existing is not None:
        return JsonResponse(status=200, data=is_existing)

    # Crawl
    try:
        response = facebook.crawl()
        response['srcUrl'] = facebook.get_url()
        write_to_db(response)
        return JsonResponse(status=200, data=response)
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data={'owner': None, 'data': []})


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
    if 'url' not in request.GET.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        tiktok = TikTok(request.GET['url'])
        data = tiktok.get_link()
        return JsonResponse(status=200, data=data)
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data=dict(url=None, headers=None, user=None))


@api_view(['POST'])
def get_insta_media(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    limit = data['limit'] if 'limit' in data.keys() else 50
    cursor = data['cursor'] if 'cursor' in data.keys() else ''

    insta = InstaAPI(data['url'])
    is_existing = find_existence(insta.get_url(), cursor)
    if is_existing is not None:
        return JsonResponse(status=200, data=is_existing)

    info = insta.crawl(limit, cursor)
    if 'data' not in info.keys():
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
            "shortcode": i['shortcode'] if i['shortcode'] is not None else None,
            "url": url,
            "isVideo": i['is_video'],
            "width": i['dimensions']['width'] if i['dimensions']['width'] is not None else None,
            "height": i['dimensions']['height'] if i['dimensions']['height'] is not None else None,
            "countComment": i['edge_media_to_comment']['count'],
            "countLike": i['edge_media_preview_like']['count']
        }
        posts.append(post)

    response = dict(cursor=info['cursor'], hasNextPage=info['has_next_page'], owner=owner, data=posts,
                    srcUrl=insta.get_url())
    write_to_db(response, cursor)

    return JsonResponse(status=200, data=response)


def find_existence(link, cursor=None):
    col = DB['media']
    if cursor is None:
        query = {'srcUrl': link}
    else:
        query = {'srcUrl': link, 'first': cursor}
    is_exit = col.find_one(query, {'_id': 0})
    if is_exit is not None:
        return is_exit
    return None


def write_to_db(data, first=None):
    col = DB['media']
    data['_expireAt'] = datetime.now()
    data['first'] = first
    col.insert_one(data)
    del data['_id']
