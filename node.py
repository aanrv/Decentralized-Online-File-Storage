#!/usr/bin/env python

# node.py

import logging
logging.basicConfig(level=logging.DEBUG)

import socket
from enum import Enum

class MessageType(Enum):
    PING = 1
    DISCONNECT = 2

class Node:

    # initialize listener socket
    def __init__(self, host=socket.gethostbyname(socket.gethostname()), port=8089):
        logging.info('initializing %s:%s' % (host, port))

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((host, port))
        self._serverSocket.listen(3)

        self._logger = logging.getLogger('%s' % str(self._serverSocket.getsockname()))
        self._logger.info('initialized')

    def __del__(self):
        self._logger.info('closing')
        self._serverSocket.close()

    def handleIncoming(self):
        connection, address = self._serverSocket.accept()
        self._logger.info('accepted %s' % str(address))
        buf = connection.recv(2)
        match buf[0]:
            case MessageType.PING:
                self._logger.info('recieved ping from %s' % str(address))
            case MessageType.DISCONNECT:
                self._logger.info('recieved disconnect from %s' % str(address))
            case _:
                self._logger.info('recieved %s from %s' % (buf, str(address)))

    # connect to a single node i.e. request host:port node adds self to its peer list
    def connect(self, host, port):
        self._logger.info('connecting to %s:%s' % (host, port))
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(str(MessageType.PING.value).encode('utf-8'))
        clientsocket.close()

    # connect to a single node i.e. request host:port node adds self to its peer list
    def disconnect(self, host, port):
        self._logger.info('disconnecting from %s:%s' % (host, port))
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(str(MessageType.DISCONNECT.value).encode('utf-8'))
        clientsocket.close()

