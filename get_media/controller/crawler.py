from django.urls import path

from get_media.service import crawler

urlpatterns = [
    path('post', crawler.download_post, name='download_post'),
    path('album', crawler.download_album, name='download_album')
]
