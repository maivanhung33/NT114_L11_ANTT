from django.urls import path

from get_media.service import user

urlpatterns = [
    path('register', user.register, name='register'),
    path('register/verify', user.verify_opt_register, name='verify'),
    path('user/reset-password', user.reset_password, name='reset-password'),
    path('user/reset-password/verify', user.verify_opt_reset_password, name='verify-reset-password'),
    path('token', user.token, name='token'),
    path('me', user.get_user, name='user-info'),
    path('me/avatar', user.avatar, name='avatar'),
    path('me/update', user.update_user, name='update-user'),
    path('me/add', user.add_to_collection, name='add-to-collection')
]
