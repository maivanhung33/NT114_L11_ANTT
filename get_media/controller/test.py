from django.urls import path

from get_media.service import test

urlpatterns = [
    path('test', test.test, name='test_controller')
]
