from django.urls import path

from get_media.service import admin

urlpatterns = [
    path('token', admin.token, name='token'),
    path('users', admin.list_user, name='list-user'),
    path('users/<str:phone>', admin.get_user, name='user-info'),
    path('users/<str:phone>/deactivate', admin.deactivate_account, name='deactivate-account'),
    path('users/<str:phone>/activate', admin.activate_account, name='activate-account'),
    path('collections', admin.list_collection, name='list-collection'),
    path('logs', admin.list_logs, name='logs'),
    path('statistics', admin.get_statistics, name='statistics')

]
