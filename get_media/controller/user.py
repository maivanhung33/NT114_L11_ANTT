from django.urls import path

from get_media.service import user

urlpatterns = [
    path('register', user.register, name='register'),
    path('register/verify', user.verify_opt_register, name='verify'),
    path('user/reset-password', user.reset_password, name='reset-password'),
    path('user/reset-password/verify', user.verify_opt_reset_password, name='verify-reset-password'),
    path('user/token', user.token, name='token'),
    path('me', user.get_user, name='user-info'),
    path('me/avatar', user.avatar, name='avatar'),
    path('me/update', user.update_user, name='update-user'),
    path('me/collections', user.collections),
    path('me/collections/<str:id>', user.collection),
    path('me/collections/<str:col_id>/items/<str:item_id>', user.remove_collection_item, name='remove-collection_item'),
    path('me/logs', user.list_logs, name='list_logs'),
]
