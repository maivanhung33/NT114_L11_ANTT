from django.urls import path

from get_media.service import media

urlpatterns = [
    path('facebook', media.get_video_facebook, name='download_facebook'),
    path('tiktok', media.get_video_tiktok, name='download_tiktok'),
    path('instagram', media.get_insta_media, name='download_instagram')
]
