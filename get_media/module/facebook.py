import json

import requests


class FaceBook:

    def __init__(self, url):
        self.__url = url

    def __validate(self):
        if self.__url.find('https://www.facebook.com/') == 0:
            self.__type = 2
            try:
                if self.__url.split('https://www.facebook.com/')[1] == '':
                    return False
                self.__page_name = self.__url.split('https://www.facebook.com/')[1]
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

    def get_link(self):
        self.__validate()
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
            item = dict(
                url=self.__get_url_video(video_id),
                thumbnail=None,
                publishTime=None,
                playCount=None
            )
            return {'owner': None, 'data': [item]}

    def __get_page_id(self):
        url = "https://www.facebook.com/ajax/bulk-route-definitions/"

        payload = 'route_urls[0]=/{}&fb_dtsg=AQG8efRGZiDH%3AAQEEcyya2P4u'.format(self.__page_name)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'c_user=100006040201647; xs=24%3AILjNxnOC6pdzeQ%3A2%3A1605231199%3A16304%3A6190%3A%3AAcUM7Y2oyTY0js50qnx2470-fzlhfBYqp4AtcVCMMQ; fr=0hnKe9SVLKEFxvJpl.AWWaOx7sXjL1xwzfYfHQC3joFCM.BfftX_.5K.AAA.0.0.BfsVTH.AWVU_ESfuOk'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        try:
            id = json.loads(response.text.replace('for (;;);', ''))
            id = id['payload']['payloads']['/' + self.__page_name]['result']['exports']['hostableView']['props'][
                'pageID']
        except Exception as e:
            return ''
        return id

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
        response = dict(
            owner={'name': self.__page_name},
            data=[]
        )
        for item in list_latest_videos:
            video_url = self.__get_url_video(item['node']['channel_tab_thumbnail_renderer']['video']['id'])
            video = dict(
                url=video_url,
                thumbnail=item['node']['channel_tab_thumbnail_renderer']['video']['image']['uri'],
                publishTime=item['node']['channel_tab_thumbnail_renderer']['video']['publish_time'],
                playCount=item['node']['channel_tab_thumbnail_renderer']['video']['play_count']
            )
            response['data'].append(video)
        return response

    def __get_url_video(self, video_id):
        url = "https://www.facebook.com/api/graphql/"

        payload = 'fb_dtsg=AQFAz9HPLA8b:AQExNUApkJQU&variables={"id":' \
                  + '"{}"'.format(video_id) \
                  + '}&doc_id=4650955718313204'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'c_user=100006040201647; spin=r.1002938977_b.trunk_t.1604846167_s.1_v.2_;'
                      + ' xs=43%3ArXUM7Zy8rJpH9Q%3A2%3A1587656106%3A16304%3A6190%3A%3AAcUWEzfBAdJBVdGiDAOb__-QTkD25AvQrT4VDpVPx9nr; fr=0hnKe9SVLKEFxvJpl.AWX6qFRbxptoYcIHn2QNHFmnYJU.BfftX_.VL.AAA.0.0.BfqPZZ.AWUnMSp93VA'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()['data']['video']['playable_url']

# _url = 'https://fb.watch/1oIoNues8H/'
# _url = 'https://www.facebook.com/nguoc.confessions'
# fb = FaceBook(_url)
# data = fb.get_link()
# print(data)
# print(fb.get_link())
