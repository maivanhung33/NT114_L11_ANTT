import requests
from TikTokApi import TikTokApi


class TikTok:
    HEADERS = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Accept': '*/*',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Dest': 'video',
        'Referer': 'https://www.tiktok.com/',
        'Accept-Language': 'en-US,en;q=0.9,bs;q=0.8,sr;q=0.7,hr;q=0.6',
        'sec-gpc': '1',
        'Range': 'bytes=0-',
    }

    def __init__(self, url):
        self.__url = url
        self.__api = TikTokApi()

    def __validate(self):
        self.__url = self.__url.split('?')[0]
        result = self.__url.find('https://www.tiktok.com/')
        if result != 0:
            return False
        elements = self.__url.split('/')
        if len(elements) < 6 or elements[4] != 'video' or elements[5] == '':
            return False
        return True

    def __get_video_id(self):
        web_id = self.__url.split('/video/')[1]
        self.__cookies = {
            'tt_webid': web_id,
            'tt_webid_v2': web_id
        }
        self.__headers = {
            'Referer': 'https://www.tiktok.com/',
            'Accept-Language': 'vi,en;q=0.9',
            'Cookie': 'tt_webid={}; tt_webid_v2={};'.format(web_id, web_id),
            'Range': 'bytes=0-'
        }
        return

    def get_link(self):
        if self.__validate():
            self.__get_video_id()
            response = requests.get(self.__url, cookies=self.__cookies, headers=self.HEADERS)
            user = self.__api.getTikTokByUrl(self.__url)['itemInfo']['itemStruct']['author']
            user = dict(username=user['nickname'],
                        avatar=user['avatarMedium'])
            return dict(url=response.text.split('"playAddr":"')[1].split('"')[0].replace(r'\u0026', '&'),
                        headers=self.__headers,
                        user=user)
        return None


# tiktok = TikTok("https://www.tiktok.com/@khang0924046415/video/6888171864833789186")
# print(tiktok.get_link())
