from re import findall
from sys import exit
from urllib.parse import unquote

import requests
from requests import get, HTTPError, ConnectionError


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
            return self.getdownlink()
        return None

    def getdownlink(self):
        url = self.__url.replace("www", "mbasic")
        try:
            r = get(url, timeout=5, allow_redirects=True)
            if r.status_code != 200:
                raise HTTPError
            a = findall("/video_redirect/", r.text)
            if len(a) == 0:
                print("[!] Video Not Found...")
                return None
            else:
                return unquote(r.text.split("?src=")[1].split('"')[0])
        except (HTTPError, ConnectionError):
            print("[x] Invalid URL")
            exit(1)
        pass

# _url = 'https://fb.watch/1oIoNues8H/'
# fb = FaceBook(_url)
# print(fb.get_link())
