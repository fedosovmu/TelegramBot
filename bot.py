from telegram_handler import *
from db_handler import *
from proxy_server_handler import *
from time import sleep
import json

class Bot:
    def __init__(self):
        self.db_handler = DbHandler()
        self.db_handler.db_connect()
        self.proxy_server_handler = ProxyServerHandler(self.db_handler)
        self.telegram_handler = TelegramHandler(self.proxy_server_handler)

    def start_loop(self):
        while True:
            last_processed_update_id = self.db_handler.select_last_processed_update_id()
            response = self.telegram_handler.get_updates(last_processed_update_id + 1)
            print(response.status_code)

            messages_count = len(response.json()['result'])
            for message in response.json()['result']:
                self.process_message(message)

            sleep(0.5)

    def process_message(self, message):
        update_id = message['update_id']
        user_id = message['message']['from']['id']
        is_bot = message['message']['from'].get('is_bot')
        first_name = message['message']['from'].get('first_name')
        last_name = message['message']['from'].get('last_name')
        username = message['message']['from'].get('username')
        language_code = message['message']['from'].get('language_code')
        date = message['message'].get('date')
        text = message['message']['text']

        self.db_handler.insert_user(username, first_name, last_name, language_code, is_bot, user_id)

        command = self.recognize_command(text)
        if command == 'hello':
            self.telegram_handler.send_message(user_id, 'Hello ' + first_name + '!')
        if command == 'search':
            self.user_search_command(user_id)
        if command == 'stop':
            self.user_stop_command(user_id)
        if command == 'none':
            self.user_none_command(user_id, text)

        self.db_handler.update_last_processed_update_id(message['update_id'])

    def user_search_command(self, user_id):
        in_search = self.db_handler.user_select_in_search(user_id)
        if (in_search):
            self.telegram_handler.send_message(user_id, 'Поиск уже идет. Для остановки поиска введите комманду \\stop')
        else:
            in_dialogue = self.db_handler.dialogue_select_is_user_in_dialogue(user_id)
            if (in_dialogue):
                self.telegram_handler.send_message(user_id, 'Невозможно начать поиск нахоядсь в диалоге. '
                                                            'Для завершения диалога введите комманду \\stop.')
            else:
                companion_id = self.db_handler.user_select_user_public_id_in_search()
                if (companion_id == None):
                    self.db_handler.user_update_in_search(user_id, True)
                    self.telegram_handler.send_message(user_id, 'Начинаю поиск.')
                else:
                    self.db_handler.user_update_in_search(companion_id, False)
                    self.db_handler.dialogue_insert(user_id, companion_id)
                    self.telegram_handler.send_message(user_id, 'Собеседник найден.')
                    self.telegram_handler.send_message(companion_id, 'Собеседник найден.')



    def user_stop_command(self, user_id):
        in_dialogue = self.db_handler.dialogue_select_is_user_in_dialogue(user_id)
        if (in_dialogue):
            companion_id = self.db_handler.dialogue_select_companion_user_public_id(user_id)
            self.db_handler.dialogue_update_finish(user_id)
            self.telegram_handler.send_message(user_id, 'Диалог завершён.')
            self.telegram_handler.send_message(companion_id, 'Ваш собеседник завершил диалог.')
        else:
            in_search = self.db_handler.user_select_in_search(user_id)
            if (in_search):
                self.db_handler.user_update_in_search(user_id, False)
                self.telegram_handler.send_message(user_id, 'Поиск остановлен.')
            else:
                self.telegram_handler.send_message(user_id, 'Поиск уже остановлен. '
                                                            'Для начала нового поиска введите комманду \\search')

    def user_none_command(self, user_id, text):
        in_dialogue = self.db_handler.dialogue_select_is_user_in_dialogue(user_id)
        if (in_dialogue):
            companion_id = self.db_handler.dialogue_select_companion_user_public_id(user_id)
            self.telegram_handler.send_message(companion_id, 'Типичный дизайнер: {}'.format(text))
        else:
            send_message_text = 'Неизвестная комманда "{}"'.format(text)
            self.telegram_handler.send_message(user_id, send_message_text)

    def recognize_command(self, text):
        if text == r'/hello':
            return 'hello'
        if text == r'/search' or text == r'/find':
            return 'search'
        if text == r'/stop':
            return 'stop'
        return 'none'