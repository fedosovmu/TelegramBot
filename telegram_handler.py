import requests
from proxy_server_handler import ProxyServerHandler
import time


class TelegramHandler:
    def __init__(self, proxy_server_handler: ProxyServerHandler):
        self.api_key = '1266321536:AAGTGU5ZRiqJscC53ZqS7ThCQ6aMBUIOvo4'
        self.proxy_server_handler = proxy_server_handler

    def get_updates(self, offset):
        url = 'https://api.telegram.org/bot{}/getUpdates?offset={}'.format(self.api_key, offset)
        while True:
            try:
                response = requests.get(url, proxies=self.proxy_server_handler.proxy_dict, timeout=10, )
                self.proxy_server_handler.success_proxy()
                break
            except requests.exceptions.ProxyError:
                self.proxy_server_handler.next_proxy()
            except requests.exceptions.ConnectTimeout:
                self.proxy_server_handler.next_proxy()
            except requests.exceptions.ReadTimeout:
                self.proxy_server_handler.next_proxy()

        if response.status_code != 200:
            raise Exception('Error TelegramHandler.GetUpdates() (status_code != 200)')

        return response

    def send_message(self, chat_id, text):
        url = 'https://api.telegram.org/bot{}/sendMessage'.format(self.api_key)
        params = {'chat_id': chat_id, 'text': text}

        while True:
            try:
                response = requests.post(url, proxies=self.proxy_server_handler.proxy_dict, verify=False, params=params)
                self.proxy_server_handler.success_proxy()
                break
            except requests.exceptions.ProxyError:
                self.next_proxy()
            except requests.exceptions.ConnectTimeout:
                self.next_proxy()
            except requests.exceptions.ReadTimeout:
                self.proxy_server_handler.next_proxy()

        if response.status_code == 200:
            print('Отправлено (' + str(chat_id) + '): ' + text)
        else:
            print('Error TelegramHandler.SendMessage() (', chat_id, '):', text)
