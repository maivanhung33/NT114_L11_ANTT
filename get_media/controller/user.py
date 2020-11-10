from django.urls import path

from get_media.service import user

urlpatterns = [
    path('register', user.register, name='register'),
    path('register/verify', user.verify_opt_register, name='verify'),
    path('user/reset-password', user.reset_password, name='reset-password'),
    path('user/reset-password/verify', user.verify_opt_reset_password, name='verify-reset-password'),
    path('token', user.token, name='token'),

]
