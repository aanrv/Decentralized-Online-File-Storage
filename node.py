# node.py

import logging

import sys
import socket
from threading import Thread
from enum import Enum

class Node:

    MessageType = Enum('MessageType', ['CONNECT', 'DISCONNECT', 'PEERS_REQUEST'])

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
                Node.MessageType.CONNECT        : self._handleConnect,
                Node.MessageType.DISCONNECT     : self._handleDisconnect,
                Node.MessageType.PEERS_REQUEST  : self._handlePeersRequest,
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
        buffer = connection.recv(4096).decode()
        self._logger.info('received buffer: %s' % buffer)
        incomingMessageType = Node.MessageType(int(buffer.split(Node.DELIM)[0]))
        self._handlers[incomingMessageType](buffer, connection)

    def _handleConnect(self, buffer, _):
        host = buffer.split(Node.DELIM)[1]
        port = int(buffer.split(Node.DELIM)[2])
        self._peers.add((host, port))
        self._logger.info('received connect from %s:%s' % (host, port))

    def _handleDisconnect(self, buffer, _):
        host = buffer.split(Node.DELIM)[1]
        port = int(buffer.split(Node.DELIM)[2])
        self._peers.remove((host, port))
        self._logger.info('recieved disconnect from %s:%s' % (host, port))

    def _handlePeersRequest(self, _, connection):
        buffer = repr(self._peers) + Node.DELIM
        connection.send(buffer.encode())

    #TODO use getaddrinfo
    #TODO use hton etc to save bytes

    # connect to a single node i.e. request host:port node adds self to its peer list
    def connect(self, host, port):
        self._logger.info('connecting to %s:%s' % (host, port))
        # TODO consider not using .value
        buffer = Node.DELIM.join(map(str, (Node.MessageType.CONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(buffer.encode())
        clientsocket.close()
        self._peers.add((host, port))

    # connect to a single node i.e. request host:port node adds self to its peer list
    def disconnect(self, host, port):
        self._logger.info('disconnecting from %s:%s' % (host, port))
        buffer = Node.DELIM.join(map(str, (Node.MessageType.DISCONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(buffer.encode())
        clientsocket.close()
        self._peers.remove((host, port))

    # TODO consider len based messages over delim based
    def peersRequest(self, host, port):
        self._logger.info('requesting peers from %s:%s' % (host, port))
        buffer = str(Node.MessageType.PEERS_REQUEST.value) + Node.DELIM
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((host, port))
        clientsocket.send(buffer.encode())
        recvbuffer = ''
        # TODO consider len based messages over delim based, searching str each time not efficient
        while Node.DELIM not in recvbuffer:
            recvbuffer += clientsocket.recv(4096).decode()
            self._logger.debug('received %s, len %s' % (recvbuffer, len(recvbuffer)))
        clientsocket.close()
        peerlist = eval(recvbuffer.split(Node.DELIM)[0])
        return peerlist

