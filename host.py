import socket
import threading

from connection_types import Client
import utils.logger as logger

HOST = 'localhost'
PORT = 9090

CLIENTS = list()

### SOCKET BINDING ###
sock = socket.socket()
sock.bind((HOST, PORT))

sock.listen(5)

logger.info('Host running : ', HOST, PORT)


def callback(data, id: int):
    message = f'[{id}] ' + data.decode('utf-8')

    color = 'white'

    # set color of message
    for client in CLIENTS:
        if client.id == id:
            color = client.color

    # send message to all clients
    for client in CLIENTS:
        if client.id == id:
            if data == b'':
                remove_member(id)
                client.conn.close()

            continue

        if data:
            client.conn.send((color + ' ' + message).encode('utf-8'))


def remove_member(id: int):
    for i in range(len(CLIENTS)):
        if CLIENTS[i].id == id:
            CLIENTS.remove(CLIENTS[i])
            break


client_id = int()

while 'LISTENING':
    try:
        conn, addr = sock.accept()
        client_id += 1

        logger.info('Connected:', addr, '| Current id : ', client_id)

        client = Client(client_id, conn, 'white')

        CLIENTS.append(client)

        thread = threading.Thread(
            target=client.loop, name=f"CLIENT {client_id}", args=(callback, remove_member))
        thread.start()
    except Exception as e:
        logger.error(e)
        conn.close()

sock.close()
