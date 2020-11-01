from django.urls import path

from get_media.service import media

urlpatterns = [
    path('download/facebook', media.getVideoFacebook, name='download_facebook'),
    path('download/tiktok', media.getVideoTiktok, name='download_tiktok'),
    path('download/instagram', media.getInstaMedia, name='download_instagram')
]
