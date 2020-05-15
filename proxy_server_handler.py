import requests
from db_handler import DbHandler


class ProxyServerHandler:
    def __init__(self, db_handler: DbHandler):
        self.db_handler = db_handler
        self.https_proxies = db_handler.select_proxies()
        self.proxy_number = 1
        self.proxy_dict = {
            "https": "https://" + self.https_proxies[self.proxy_number][0]
        }

    def next_proxy(self):
        print('Ошибка прокси сервера', self.https_proxies[self.proxy_number][0])
        self.db_handler.proxy_update_failure(self.https_proxies[self.proxy_number][1])
        self.proxy_number = (self.proxy_number + 1) % len(self.https_proxies)
        self.proxy_dict = {
            "https": "https://" + self.https_proxies[self.proxy_number][0]
        }

    def success_proxy(self):
        self.db_handler.proxy_update_success(self.https_proxies[self.proxy_number][1])