import psycopg2


class DbHandler:
    def db_connect(self):
        self.connection = psycopg2.connect(dbname='telegram_bot', user='postgres', password='postgres',
                                           host='localhost', port='5434')
        self.cursor = self.connection.cursor()

    # Пользователи
    def select_users(self):
        self.cursor.execute('SELECT * FROM bot.user')
        rows = self.cursor.fetchall()

        print('clients: ')
        for row in rows:
            print('username: ', row)

    def insert_user(self, username, first_name, last_name, language_code, is_bot, public_id):
        sql_query = """INSERT INTO bot.user (username, first_name, last_name, language_code, is_bot, public_id)
                    SELECT %s, %s, %s, %s, %s, %s
                    WHERE %s NOT IN (SELECT public_id FROM bot.user)"""
        self.cursor.execute(sql_query, (username, first_name, last_name, language_code, is_bot, public_id, str(public_id)))
        self.connection.commit()
        print('user ({}, {}, {}, {}) inserted'.format(username, first_name, last_name, public_id))

    def user_select_in_search(self, public_user_id):
        self.cursor.execute('SELECT in_search FROM bot.user WHERE public_id = %s', (str(public_user_id),))
        rows = self.cursor.fetchall()
        return bool(rows[0][0])

    def user_update_in_search(self, public_user_id, in_search):
        self.cursor.execute('UPDATE bot.user SET in_search = %s WHERE public_id = %s', (in_search, str(public_user_id)))
        self.connection.commit()
        print('update "in_search" ({}) to {}'.format(public_user_id, in_search))

    def user_select_user_public_id_in_search(self):
        self.cursor.execute('SELECT public_id FROM bot.user WHERE in_search')
        rows = self.cursor.fetchall()
        if (len(rows) == 0):
            result = None
        else:
            result = rows[0][0]
        return result


    # Диалоги
    def dialogue_select_is_user_in_dialogue(self, user_public_id):
        self.cursor.execute('WITH user_id AS (SELECT user_id FROM bot.user WHERE public_id = %s) '
                            'SELECT (count(1) > 0) AS "user_in_dialogue" FROM bot.dialogue '
                            'WHERE NOT is_finished AND '
                            '(user_one_id = (SELECT user_id FROM user_id) '
                            'OR user_two_id = (SELECT user_id FROM user_id))', (str(user_public_id),))
        rows = self.cursor.fetchall()
        return bool(rows[0][0])

    def dialogue_insert(self, user_one_public_id, user_two_public_id):
        self.cursor.execute('INSERT INTO bot.dialogue(user_one_id, user_two_id) '
                            'SELECT '
                            '(SELECT user_id FROM bot.user WHERE public_id = %s) AS "user_one", '
                            '(SELECT user_id FROM bot.user WHERE public_id = %s) AS "user_two"',
                            (str(user_one_public_id), str(user_two_public_id)))
        self.connection.commit()
        print('dialogue inserted')

    def dialogue_select_companion_user_public_id(self, user_public_id):
        self.cursor.execute('WITH user_id AS (SELECT user_id FROM bot.user WHERE public_id = %s'
                            '), companion_id AS ('
                            'SELECT user_one_id AS "companion_id" FROM bot.dialogue '
                            'WHERE NOT is_finished AND user_two_id = (SELECT user_id FROM user_id) '
                            'UNION ALL '
                            'SELECT user_two_id AS "companion_id" FROM bot.dialogue '
                            'WHERE NOT is_finished AND user_one_id = (SELECT user_id FROM user_id)) '
                            'SELECT public_id FROM bot.user WHERE user_id = (SELECT companion_id FROM companion_id)',
                            (str(user_public_id),))
        rows = self.cursor.fetchall()
        return rows[0][0]

    def dialogue_update_finish(self, user_public_id):
        self.cursor.execute('WITH user_id AS (SELECT user_id FROM bot.user WHERE public_id = %s) '
                            'UPDATE bot.dialogue SET finish_date = NOW(), is_finished = TRUE '
                            'WHERE NOT is_finished AND '
                            '(user_one_id = (SELECT user_id FROM user_id) '
                            'OR user_two_id = (SELECT user_id FROM user_id))',
                            (str(user_public_id),))
        self.connection.commit()
        print('dialogue update finish')

    # Данные о последнем update-е
    def select_last_processed_update_id(self):
        self.cursor.execute('SELECT last_processed_update_id FROM bot.bot_data LIMIT 1')
        rows = self.cursor.fetchall()
        return int(rows[0][0])

    def update_last_processed_update_id(self, last_processed_update_id):
        self.cursor.execute('UPDATE bot.bot_data SET last_processed_update_id=%s', (str(last_processed_update_id),))
        self.connection.commit()
        print('update "last_processed_update_id" to', last_processed_update_id)

    # Прокси сервера
    def select_proxies(self):
        self.cursor.execute('SELECT ip_address, proxy_server_id FROM bot.proxy_server WHERE is_relevant '
                            'ORDER BY failure_in_row, last_check_date LIMIT 100')
        rows = self.cursor.fetchall()
        return rows

    def proxy_update_success(self, proxy_id):
        self.cursor.execute('UPDATE bot.proxy_server '
                            'SET last_check_date = NOW(), failure_in_row = 0 '
                            'WHERE proxy_server_id = %s', (proxy_id,))
        self.connection.commit()

    def proxy_update_failure(self, proxy_id):
        self.cursor.execute('UPDATE bot.proxy_server '
                            'SET last_check_date = NOW(), failure_in_row = failure_in_row + 1 '
                            'WHERE proxy_server_id = %s', (proxy_id,))
        self.connection.commit()

    def proxy_update_all_failure_in_row_to_zero(self):
        self.cursor.execute('UPDATE bot.proxy_server SET failure_in_row = 0')
        self.connection.commit()

    def proxy_insert(self):
        pass