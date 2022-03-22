from typing import Any
import utils.logger as logger
from utils.vars import font_colors

class Client:
    PREFIX = '[HOST]'

    def __init__(self, id : str, conn, color : str):
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

    def command_handler(self, message : str) -> Any:
        """ Actions in chat triggered by specific commands """

        set_nickname = 'SET_NICKNAME'
        current_nickname = 'NICKNAME'
        set_color = 'SET_COLOR'
        current_color = 'COLOR'

        splited_message = message.split()

        if set_nickname in message:
            nickname = splited_message[1]

            logger.info(f'{self.id} changed nickname to {nickname}')
            self.id = nickname

            self.send(f'Your current nickname : {self.id}')

            return self.id

        if set_color in message:
            _color = splited_message[-1]

            if _color in font_colors:
                self.color = _color
                logger.info(f'{self.id} changed color to {self.color}')
            else:
                self.send(f'{_color} color not found')

            self.send(f'Your current font color : {self.color}')

            return self.color

        if message == current_color:
            self.send(f'Your current font color : {self.color}')

            return self.color

        if message == current_nickname:
            self.send(f'Your current nickname : {self.id}')

            return self.id

        return False

    def send(self, message):
        self.conn.send(self._admin_msg(message))

    def _admin_msg(self, message):
        """ Shape Admin Message with prefix and encoding """
        return (f'yellow {self.PREFIX} {message}').encode('utf-8')

           