import json

from django.http import JsonResponse
from rest_framework.decorators import api_view
from get_media.module.facebook import FaceBook
from get_media.module.instagram import InstaAPI
from get_media.module.tiktok import TikTok


@api_view(['POST'])
def getVideoFacebook(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        facebook = FaceBook(data['url'])
        return JsonResponse(status=200, data={"url": facebook.get_link()})
    except:
        return JsonResponse(status=200, data=dict(url=None))


@api_view(['POST'])
def getVideoTiktok(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    try:
        tiktok = TikTok(data['url'])
        return JsonResponse(status=200, data=tiktok.get_link())
    except:
        return JsonResponse(status=200, data=dict(url=None, headers=None, user=None))


@api_view(['POST'])
def getInstaMedia(request):
    data: dict = json.loads(request.body.decode('utf-8'))
    if 'url' not in data.keys():
        return JsonResponse(data={'message': 'URL_REQUIRED'}, status=400)
    print(data['url'])
    insta = InstaAPI(data['url'])
    info = insta.get()
    print(insta.get())
    if 'data' not in info.keys():
        owner: dict = {
            "avatar": None,
            "username": None,
            "fullname": None,
            "countPost": None,
            "countFollowedBy": None
        }
        posts: list = [{
            "shortcode": None,
            "url": None,
            "isVideo": None,
            "width": None,
            "height": None,
            "countComment": None,
            "countLike": None
        }]
        return JsonResponse(status=200, data=dict(owner=owner, data=posts))
    if info['user'] is not None:
        owner: dict = {
            "avatar": info['user']['profile_pic_url_hd'],
            "username": info['user']['username'],
            "fullname": info['user']['full_name'],
            "countPost": info['user']['edge_follow']['count'],
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
    return JsonResponse(status=200, data=dict(owner=owner, data=posts))
