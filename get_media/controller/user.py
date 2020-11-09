from django.urls import path

from get_media.service import user

urlpatterns = [
    path('register', user.register, name='register'),
    path('token', user.token, name='token'),
    path('verify', user.confirm_otp, name='verify'),

]
