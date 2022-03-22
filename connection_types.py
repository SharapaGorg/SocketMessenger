from ast import Str
from typing import Any, Dict, List
from xmlrpc.client import Boolean
import utils.logger as logger
from utils.vars import font_colors
from os.path import join
import json

USERS = join('users', 'users.json')


class Client:
    PREFIX = '[HOST]'

    def __init__(self, id: str, conn, color: str):
        self.id = id
        self.conn = conn
        self.color = color

    def loop(self, callback, remove_member):
        while 'LISTENING':
            try:
                data = self.conn.recv(1024)
                decoded_data = data.decode('utf-8')

                if decoded_data == 'exit' or not data:
                    remove_member(self.id)
                    self.conn.close()
                    break

                if self.command_handler(decoded_data):
                    continue

                callback(data, self.id)

            except Exception as e:
                if e.args[0] != 10054:
                    logger.error('[Client.loop]' + str(e))

                remove_member(self.id)
                self.conn.close()
                break

    def command_handler(self, message: str) -> Any:
        """ Actions in chat triggered by specific commands """

        set_nickname = 'SET_NICKNAME'
        current_nickname = 'NICKNAME'
        set_color = 'SET_COLOR'
        current_color = 'COLOR'
        login_user = 'LOG'
        reg_user = 'REG'

        splited_message = message.split()

        if set_nickname in message:
            nickname = splited_message[1]

            if self._set_nickname(nickname):
                logger.info(f'{self.id} changed nickname to {nickname}')
                self.id = nickname

            self.send(f'Your current nickname : {self.id}')

            return self.id

        if set_color in message:
            _color = splited_message[-1]

            if _color in font_colors:
                self.color = _color
                self._set_color(self.color)
                logger.info(f'{self.id} changed color to {self.color}')
            else:
                self.send(f'{_color} color not found')

            self.send(f'Your current font color : {self.color}')

            return self.color

        if login_user in message and len(splited_message) == 3:
            username = splited_message[1]
            password = splited_message[2]

            self._log_user(username, password)
            return self.id

        if reg_user in message and len(splited_message) == 3:
            username = splited_message[1]
            password = splited_message[2]

            if self._reg_user(username, password):
                self._log_user(username, password)
            return self.id

        if message == current_color:
            self.send(f'Your current font color : {self.color}')

            return self.color

        if message == current_nickname:
            self.send(f'Your current nickname : {self.id}')

            return self.id

        return False

    def _set_nickname(self, username : str) -> Boolean:
        users = self._parse_users()

        if self.id not in users:
            self.send(f'You have to stay logged in to change nickname')
            return False

        if username in users:
            self.send(f'Username {username} already exists')
            return False

        users[username] = users[self.id]
        users.pop(self.id)

        with open(USERS, 'w',encoding='utf-8') as write_stream:
            json.dump(users, write_stream, indent=4, sort_keys=True)

        return True

    def _set_color(self, color : str):
        users = self._parse_users()

        try:
            users[self.id]['COLOR'] = color
            self._edit_users(self.id, color=color)
        except:
            pass

    def _reg_user(self, username: str, password: str) -> Boolean:
        users = self._parse_users()

        if username in users:
            self.send(
                f'Username {username} already exists, try one another')

            return False

        self._edit_users(username, password, 'white', users)

        self.send(f'Account {username} successfully created')
        return self.id

    def _log_user(self, username: str, password: str):
        users = self._parse_users()

        if username not in users:
            self.send(f'Account {username} does not exist')
            return False

        if users[username]['PASSWORD'] != password:
            self.send(f'Incorrect password')
            return False

        self.id = username
        self.color = users[username]['COLOR']

        self.send(f'Successfully logged in as {self.id}')
        return self.id

    def _parse_users(self) -> Dict:
        with open(USERS, 'r', encoding='utf-8') as read_stream:
            data = read_stream.read()

            return json.loads(data)

    def _edit_users(self, username : str, password : str = None, color : str = None, users : list = None):
        if not users:
            users = self._parse_users()

        with open(USERS, 'w', encoding='utf-8') as write_stream:
            if not users.get(username):
                users[username] = dict()

            if password:
                users[username]['PASSWORD'] = password

            if color:
                users[username]['COLOR'] = color

            json.dump(users, write_stream, indent=4, sort_keys=True)

    def send(self, message):
        self.conn.send(self._admin_msg(message))

    def _admin_msg(self, message):
        """ Shape Admin Message with prefix and encoding """
        return (f'yellow {self.PREFIX} {message}').encode('utf-8')
