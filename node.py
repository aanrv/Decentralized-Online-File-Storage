#!/usr/bin/env python

# node.py

import logging

import sys
import socket
from threading import Thread
from enum import Enum

class MessageType(Enum):
    CONNECT = 1
    DISCONNECT = 2

class Node:

    DELIM = '\1'

    # initialize listener socket
    def __init__(self, host=socket.gethostbyname(socket.gethostname()), port=8089):
        logging.basicConfig(level=logging.DEBUG)
        logging.info('initializing %s:%s' % (host, port))

        self._peers = set()

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((host, port))
        self._serverSocket.listen(3)

        # start server thread
        self._serverThread = Thread(target=self.handleIncoming)
        self._serverThread.start()

        self._handlers = {
                MessageType.CONNECT     : self._handleConnect,
                MessageType.DISCONNECT  : self._handleDisconnect,
        }

        self._logger = logging.getLogger('%s' % str(self._serverSocket.getsockname()))
        self._logger.info('initialized')

    def __del__(self):
        self._logger.info('closing')
        self._serverSocket.close()

    def handleIncoming(self):
        while True:
            self._handleIncoming()

    def _handleIncoming(self):
        connection, address = self._serverSocket.accept()
        self._logger.info('accepted %s' % str(address))
        buffer = connection.recv(1024).decode()
        self._logger.info('received buffer: %s' % buffer)
        incomingMessageType = MessageType(int(buffer.split(Node.DELIM)[0]))
        self._handlers[incomingMessageType](buffer)

    def _handleConnect(self, buffer):
        _, address, port = buffer.split(Node.DELIM)[0:3]
        self._peers.add((address, port))
        self._logger.info('received connect from %s:%s' % (address, port))

    def _handleDisconnect(self, buffer):
        _, address, port = buffer.split(Node.DELIM)[0:3]
        self._peers.remove((address, port))
        self._logger.info('recieved disconnect from %s:%s' % (address, port))

    #TODO use getaddrinfo
    #TODO use hton etc to save bytes

    # connect to a single node i.e. request host:port node adds self to its peer list
    def connect(self, host, port):
        self._logger.info('connecting to %s:%s' % (host, port))
        buffer = Node.DELIM.join(map(str, (MessageType.CONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(buffer.encode())
        clientsocket.close()

    # connect to a single node i.e. request host:port node adds self to its peer list
    def disconnect(self, host, port):
        self._logger.info('disconnecting from %s:%s' % (host, port))
        buffer = Node.DELIM.join(map(str, (MessageType.DISCONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(buffer.encode())
        clientsocket.close()

