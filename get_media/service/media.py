import json

import requests
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view

from get_media.module.facebook import FaceBook
from get_media.module.instagram import InstaAPI
from get_media.module.tiktok import TikTok


@api_view(['POST'])
def get_video_facebook(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        facebook = FaceBook(data['url'])
        return JsonResponse(status=200, data=facebook.get_link())
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data={'owner': None, 'data': []})


@api_view(['POST'])
def get_video_tiktok(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        tiktok = TikTok(data['url'])
        data = tiktok.get_link()
        response = requests.get(data['url'], headers=data['headers'])
        return HttpResponse(response.content, content_type='video/mp4')
        # return JsonResponse(status=200, data=tiktok.get_link())
    except Exception as e:
        print(e)
        return JsonResponse(status=200, data=dict(url=None, headers=None, user=None))


@api_view(['POST'])
def get_insta_media(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    insta = InstaAPI(data['url'])

    limit = data['limit'] if 'limit' in data.keys() else 50
    cursor = data['cursor'] if 'cursor' in data.keys() else ''
    info = insta.get(limit, cursor)
    if 'data' not in info.keys():
        return JsonResponse(status=200, data=dict(owner=None, data=None))
    owner = None
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
    return JsonResponse(
        status=200,
        data=dict(
            cursor=info['cursor'],
            hasNextPage=info['has_next_page'],
            owner=owner,
            data=posts)
    )
