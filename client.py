#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import socket
import sys
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

# dev
sock.connect(('localhost', 9090))
# prod
# sock.connect(('185.127.224.67', 9002))

console = Console()

def receive_data(conn):
    try:
        while True:
            _data = conn.recv(1024)
            data = _data.decode('utf-8').split()
            color, author, message = data[0], data[1], ' '.join(data[2:])

            if author == '[HOST]':
                content = Panel(Text(message, justify='center'))
                console.print(content)
            else:
                content = ANSI(font_colors.get(color) + author + ' ' + message + font_colors.get('white'))
                print_formatted_text(content)
            
    except:
        # logger.warning('Client aborted')
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

            if message == 'exit':
                break

        except (EOFError, KeyboardInterrupt):
            return


async def main():
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
