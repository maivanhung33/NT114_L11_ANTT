import fbdown
import requests


class FaceBook:

    def __init__(self, url):
        self.__url = url

    def __validate(self):
        result = self.__url.find('https://fb.watch/')
        if result != 0:
            return False
        element = self.__url.split('/')
        if len(element) < 3 or element[3] == '':
            return False
        self.__url = 'https://fb.watch/' + element[3] + "/"
        self.__url = requests.get(self.__url).url
        return True

    def get_link(self):
        if self.__validate():
            return fbdown.getdownlink(self.__url)
        return None


# _url = 'https://fb.watch/1oIoNues8H/'
# fb = FaceBook(_url)
# print(fb.get_link())
