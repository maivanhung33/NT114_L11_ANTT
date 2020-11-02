import requests


class InstaAPI:
    BASE_URL = "https://www.instagram.com/graphql/query/"
    USER_INFO_URL = "https://www.instagram.com/"

    def __init__(self, url):
        self.__url = url
        self.__type = ''
        if self.__validate():
            self.__header = {'cookie': 'sessionid=5711537494:6CgNGeSaClp9xB:8;',
                             'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
            self.__payload = {}
            self.__query_param = {}

    def __get_media(self, user_id, cursor: str):
        cursor = cursor.replace("=", '')
        cursor += '%3D%3D' if cursor != '' else ''
        url = self.BASE_URL + r'?query_hash=e769aa130647d2354c40ea6a439bfc08&variables=%7B%22id%22%3A%22'
        url += str(user_id) + r'%22%2C%22first%22%3A50%2C%22after%22%3A%22'
        url += str(cursor) + r'%22%7D'
        return requests.get(url, headers=self.__header, timeout=3).json()

    def __get_post(self, short_code):
        url = self.BASE_URL + r'?query_hash=a92f76e852576a71d3d7cef4c033a95e&variables=%7B%22shortcode%22%3A%22'
        url += str(short_code) + r'%22%7D'
        return requests.get(url, headers=self.__header, timeout=3).json()

    def __get_user_info(self, user_name):
        url = self.USER_INFO_URL + str(user_name) + r'/?__a=1'
        data = requests.get(url, headers=self.__header, timeout=3)
        return data.json()

    def __validate(self):
        elements = self.__url.split('/')
        if len(elements) < 4:
            return False
        domain = elements[2]
        if domain == 'www.instagram.com':
            if elements[3] == 'p' and len(elements) > 4:
                self.__type = 'POST'
                self.__shortcode = elements[4]
                self.__url = self.BASE_URL + 'p/' + self.__shortcode
                return True
            elif elements[3] != 'p' and len(elements) > 3:
                self.__type = 'PROFILE'
                self.__username = elements[3]
                self.__url = self.BASE_URL + elements[3]
                return True
        return False

    def add_session(self, session_id: str):
        self.__header = {'cookie': 'sessionid={};'.format(session_id),
                         'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

    def get(self):
        if self.__type == 'POST':
            post = self.__get_post(self.__shortcode)
            if post['data']['shortcode_media'] is None:
                return {}
            return dict(user=None,
                        data=[post['data']['shortcode_media']])
        if self.__type == 'PROFILE':
            user = self.__get_user_info(self.__username)
            if user == {}:
                return {}
            del user['graphql']['user']['edge_felix_video_timeline']
            del user['graphql']['user']['edge_owner_to_timeline_media']
            del user['graphql']['user']['edge_saved_media']
            del user['graphql']['user']['edge_media_collections']

            user_id = user['graphql']['user']['id']
            cursor = ''
            data = []
            while cursor is not None:
                response = self.__get_media(user_id, cursor)
                edges = response['data']['user']['edge_owner_to_timeline_media']['edges']
                for edge in edges:
                    data.append(edge['node'])
                cursor = response['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
                # cursor = None
            return dict(user=user['graphql']['user'],
                        data=data)
        return None


# insta = InstaAPI('https://www.instagram.com/')
# print(insta.get())
