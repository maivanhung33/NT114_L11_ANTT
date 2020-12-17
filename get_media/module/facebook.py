import requests


class FaceBook:

    def __init__(self, url):
        self.__url = url
        self.__validate()

    def __validate(self):
        if self.__url.find('https://www.facebook.com/') == 0:
            self.__type = 2
            try:
                if self.__url.split('https://www.facebook.com/')[1] == '':
                    return False
                self.__page_name = self.__url.split('https://www.facebook.com/')[1].split('/')[0]
                self.__url = 'https://www.facebook.com/' + self.__page_name
            except Exception as e:
                return False
        if self.__url.find('https://fb.watch/') == 0:
            self.__type = 1
            element = self.__url.split('/')
            if len(element) < 3 or element[3] == '':
                return False
            self.__url = 'https://fb.watch/' + element[3] + "/"
            self.__url = requests.get(self.__url).url
            return True

    def get_url(self):
        return self.__url

    def crawl(self, limit=10, cursor=None):
        if self.__type == 2:
            page_id = self.__get_page_id()
            return self.__get_latest_videos(page_id, limit, cursor)
        if self.__type == 1:
            try:
                video_id = self.__url.split('/videos/')[1].replace('/', '')
                if video_id == '':
                    return {'owner': None, 'data': []}
                video = FaceBook.get_video_info(video_id)
                owner = FaceBook.get_owner_info(video['owner_id'])
                owner['avatar'] = self.get_avatar(video['owner_id'])
                item = dict(
                    id=video_id,
                    source=self.get_url(),
                    url=FaceBook.get_download_url(video_id),
                    thumbnail=video['thumbnail'],
                    title=video['title'])
                return {'owner': owner, 'data': [item]}
            except Exception as e:
                raise e
                # print('[FB] error ' + e.__str__())
                # return {'owner': None, 'data': []}

    def __get_page_id(self):
        page_html = requests.get(self.__url).text
        if page_html.find('\"fb://page/?id=') == -1:
            return ''
        page_id = page_html.split('"fb://page/?id=')[1].split("\"")[0]
        return page_id

    def __get_latest_videos(self, page_id, limit=10, cursor=None):
        try:
            videos = self.get_latest_videos(page_id, limit, cursor)

            owner = FaceBook.get_owner_info(page_id)
            owner['avatar'] = self.get_avatar(page_id)

            response = dict(owner=owner, data=[], cursor=videos['cursor'], hasNextPage=videos['hasNextPage'])

            for video in videos['data']:
                video_url = FaceBook.get_download_url(video['source'].split('/videos/')[1].split('/')[0])
                video['url'] = video_url
                response['data'].append(video)

            return response
        except Exception as e:
            print('[FB] error ' + e.__str__())
            return dict(owner=None, data=[], cursor=None, hasNextPage=None)

    @staticmethod
    def get_latest_videos(page_id, limit=10, cursor=None):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'variables={' \
                  + '\"count\":{}'.format(limit) \
                  + ',\"scale\":1,\"useDefaultActor\":false,\"id\":\"{}\"'.format(page_id)
        payload += ',cursor:\"{}\"'.format(cursor) if cursor is not None else ''
        payload += '}&doc_id=5073419716001809'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            response = response.json()
        except Exception as e:
            print('[FB] error ' + e.__str__())
            return {'data': [], 'cursor': None, 'hasNextPage': False}

        videos = response['data']['node']['latest_videos']['edges']
        response = {
            'data': [],
            'cursor': response['data']['node']['latest_videos']['page_info']['end_cursor'],
            'hasNextPage': response['data']['node']['latest_videos']['page_info']['has_next_page'],
        }
        for item in videos:
            video = {
                'id': item['node']['id'],
                'source': item['node']['url'],
                'title': item['node']['savable_title']['text'],
                'thumbnail': item['node']['VideoThumbnailImage']['uri'],
                'playCount': item['node']['play_count'],
                'publishTime': item['node']['publish_time']}
            response['data'].append(video)
        return response

    @staticmethod
    def get_video_info(video_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'fb_dtsg=AQFAz9HPLA8b:AQExNUApkJQU&variables={"id":\"' + video_id + '\"}&doc_id=3505988849454782'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.request("POST", url, headers=headers, data=payload)
        return dict(thumbnail=response.json()['data']['video']['image']['uri'],
                    owner_id=response.json()['data']['video']['owner']['id'],
                    title=response.json()['data']['video']['title']['text'])

    @staticmethod
    def get_download_url(video_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'fb_dtsg=AQFAz9HPLA8b:AQExNUApkJQU&variables={"id":' \
                  + '"{}"'.format(video_id) \
                  + '}&doc_id=4650955718313204'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        request_response = requests.request("POST", url, headers=headers, data=payload)
        return request_response.json()['data']['video']['playable_url']

    @staticmethod
    def get_owner_info(page_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'variables={"pageID":\"' + page_id + '\"}&doc_id=1766735040109284'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.request("POST", url, headers=headers, data=payload)
        follow = response.json()['data']['page']['video_page_social_context']['sentence']['text']

        url = "https://www.facebook.com/api/graphql/"

        payload = 'variables={\"pageID\":\"' + page_id + '\",\"showContextualColor\":false}&doc_id=2915378275224907'

        response = requests.request("POST", url, headers=headers, data=payload)

        try:
            name = response.json()['data']['page']['name']
            websites = response.json()['data']['page']['websites']
            about = response.json()['data']['page']['about']['text']
            page_video = response.json()['data']['page']['page_video']['page_video_count']
        except Exception as e:
            print('[FB] error ' + e.__str__())
            name = websites = about = page_video = None

        return dict(username=name, follow=follow, websites=websites, about=about, count_video=page_video)

    @staticmethod
    def get_avatar(id):
        try:
            url = requests.get('https://www.facebook.com/{}'.format(id)).url
            page_html = requests.get(url).text
            if 'type\":\"Person\"' not in page_html:
                avatar = page_html \
                    .split('\"PagesProfilePictureEditMenu\"')[1] \
                    .split('\"uri\":\"')[1].split('\"')[0] \
                    .replace('\\', '')
            else:
                avatar = page_html.split('\"image\":\"')[1].split('\"')[0].replace('\\', '')
            return avatar
        except:
            return None

# print(FaceBook.get_latest_videos("194149144034882"))
# 194149144034882
# print(FaceBook.get_page_info('194149144034882'))
# print(requests.get('https://www.facebook.com/trollbongda').text)
# page_html = requests.get('https://www.facebook.com/trollbongda').text
# _url = 'https://fb.watch/1oIoNues8H/'
# _url = 'https://www.facebook.com/nguoc.confessions'
# fb = FaceBook(_url)
# data = fb.get_link()
# print(data)
# print(fb.get_link())
# page_html = requests.get('https://www.facebook.com/Kaka/').text
# print(FaceBook.get_avatar('194149144034882'))
