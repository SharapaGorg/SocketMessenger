#!/usr/bin/env python
# -*- coding: utf-8 -*-

from asyncore import write
import json
from textwrap import indent


try:
    import asyncio
    import socket
    import sys, os
    import threading
    import utils.logger as logger
    from prompt_toolkit.shortcuts import PromptSession
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit import ANSI, print_formatted_text

    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel

    from utils.vars import font_colors

    sock = socket.socket()

    if len(sys.argv) < 2:
        logger.warning('Ты недостоин')
        sys.exit()

    if sys.argv[1] == '--dev':
        sock.connect(('localhost', 9090))
    if sys.argv[1] == '--prod':    
        sock.connect(('185.127.224.67', 9002))

    console = Console()

    USER = 'autocomplete'
    USER_PATH = os.path.join(USER, 'secret.json')
    last_message = str()

    def receive_data(conn):
        try:
            while True:
                _data = conn.recv(1024)
                data = _data.decode('utf-8').split()
                color, author, message = data[0], data[1], ' '.join(data[2:])

                if author == 'HOST':
                    content = Panel(Text(message, justify='center'))
                    console.print(content)

                    if 'logged' in message:
                        # saving data about account
                        if not os.path.exists(USER):
                            os.mkdir(USER)

                        command, username, password = last_message.split()

                        with open(USER_PATH, 'w', encoding='utf-8') as write_stream:
                            data = json.dumps({username : password}, indent=4, sort_keys=True)

                            write_stream.write(data)

                else:
                    content = ANSI(font_colors.get(color) + author + ' ' + message + font_colors.get('white'))
                    print_formatted_text(content)

        except:
            pass

    receive_thread_ = threading.Thread(target=receive_data, args=[
        sock], name='Socket-Data-Receiver 1', daemon=True)


    async def receiver():
        try:
            receive_thread_.start()

        except asyncio.CancelledError:
            logger.warning("Background receive task cancelled.")


    async def typing():

        session = PromptSession("[You]: ")

        while True:
            try:
                message = await session.prompt_async()

                sock.send(message.encode('utf-8'))
                global last_message
                last_message = message

                if message == 'exit':
                    break

            except (EOFError, KeyboardInterrupt):
                return


    async def main():
        # if os.path.exists(USER_PATH):
        #     # autologin
        #     with open(USER_PATH, 'r', encoding='utf-8') as read_stream:
        #         data = json.loads(read_stream.read())

        #         command = 'LOG'
        #         username = list(data.keys())[0]
        #         password = data.get(username)

        #         sock.send(' '.join([command, username, password]).encode('utf-8'))

        with patch_stdout():
            background_receiver = asyncio.create_task(receiver())

            try:
                await typing()
            finally:
                background_receiver.cancel()

            print('Quitting chatting. Bye')

            sock.close()
            sys.exit()


    asyncio.run(main())
except Exception as e:
    logger.error(e)
