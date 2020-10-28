from django.urls import path

from get_media.service import user

urlpatterns = [
    path('register', user.register, name='register'),
    path('login', user.login, name='login'),
    path('info', user.info, name='info')
]
