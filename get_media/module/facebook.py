import json

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

    def crawl(self):
        if self.__type == 2:
            page_id = self.__get_page_id()
            return self.__get_latest_videos(page_id)
        if self.__type == 1:
            try:
                video_id = self.__url.split('/videos/')[1].replace('/', '')
            except:
                return {'owner': None, 'data': []}
            if video_id == '':
                return {'owner': None, 'data': []}
            video = FaceBook.get_video_info(video_id)
            item = dict(
                url=FaceBook.get_url_video(video_id),
                thumbnail=video['thumbnail'],
                title=video['title'])
            return {'owner': None, 'data': [item]}

    def __get_page_id(self):
        page_html = requests.get(self.__url).text
        if page_html.find('\"fb://page/?id=') == -1:
            return ''
        page_id = page_html.split('"fb://page/?id=')[1].split("\"")[0]
        self.__page_avatar = page_html \
            .split('\"PagesProfilePictureEditMenu\"')[1] \
            .split('\"uri\":\"')[1].split('\"')[0] \
            .replace('\\', '')
        return page_id

    def __get_latest_videos(self, page_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'fb_dtsg=AQEJJzgt5tOo:AQHeQHHfKUaS' + \
                  '&fb_api_caller_class=RelayModern' + \
                  '&fb_api_req_friendly_name=CometSinglePageChannelTabRootQuery' + \
                  '&variables={"UFI2CommentsProvider_commentsKey":"CometSinglePageChannelTabRoot",' + \
                  '"displayCommentsContextEnableComment":null,"displayCommentsContextIsAdPreview":null,' + \
                  '"displayCommentsContextIsAggregatedShare":null,"displayCommentsContextIsStorySet":null,' + \
                  '"displayCommentsFeedbackContext":null,"feedLocation":"PAGE_TIMELINE","feedbackSource":72,' + \
                  '"focusCommentID":null,"pageID":"{}","scale":4,"useDefaultActor":false'.format(page_id) + \
                  '}&server_timestamps=true' + \
                  '&doc_id=3712140348836399'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.text.replace('\r\n', ',').replace(' ', '').replace('\n', '').replace('\r', '').replace('$',
                                                                                                                   '')
        response = '{\"content\":[' + response + ']}'
        json_data = json.loads(response)

        list_latest_videos = []
        for item in json_data['content']:
            if 'label' in item.keys() \
                    and item['label'] == 'CometSinglePageChannelTabRootQuerydeferCometChannelTabLatestVideosCard_page':
                list_latest_videos = item['data']['latest_videos']['edges']
                break

        owner = FaceBook.get_page_info(page_id)
        owner['avatar'] = self.__page_avatar
        response = dict(owner=owner, data=[])
        for item in list_latest_videos:
            video_url = FaceBook.get_url_video(item['node']['channel_tab_thumbnail_renderer']['video']['id'])
            video = dict(url=video_url,
                         title=FaceBook.get_video_info(item['node']['channel_tab_thumbnail_renderer']['video']['id'])[
                             'title'],
                         thumbnail=item['node']['channel_tab_thumbnail_renderer']['video']['image']['uri'],
                         publishTime=item['node']['channel_tab_thumbnail_renderer']['video']['publish_time'],
                         playCount=item['node']['channel_tab_thumbnail_renderer']['video']['play_count'])
            response['data'].append(video)

        return response

    @staticmethod
    def get_video_info(video_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'fb_dtsg=AQFAz9HPLA8b:AQExNUApkJQU&variables={"id":\"' + video_id + '\"}&doc_id=3505988849454782'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.request("POST", url, headers=headers, data=payload)

        return dict(thumbnail=response.json()['data']['video']['image']['uri'],
                    owner_id=response.json()['data']['video']['owner']['id'],
                    title=response.json()['data']['video']['title']['text'])

    @staticmethod
    def get_url_video(video_id):
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
    def get_page_info(page_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'variables={"pageID":\"' + page_id + '\"}&doc_id=1766735040109284'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        follow = response.json()['data']['page']['video_page_social_context']['sentence']['text']

        url = "https://www.facebook.com/api/graphql/"

        payload = 'variables={\"pageID\":\"' + page_id + '\",\"showContextualColor\":false}&doc_id=2915378275224907'

        response = requests.request("POST", url, headers=headers, data=payload)

        name = response.json()['data']['page']['name']
        websites = response.json()['data']['page']['websites']
        about = response.json()['data']['page']['about']['text']
        page_video = response.json()['data']['page']['page_video']['page_video_count']

        return dict(
            username=name, follow=follow, websites=websites, about=about, count_video=page_video
        )

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
