# node.py

import logging

import sys
import socket
from threading import Thread
from enum import Enum

class Node:

    MessageType = Enum('MessageType', [
        'CONNECT',
        'DISCONNECT',
        'PEERS_REQUEST'
    ])

    DELIM = '\1'

    # initialize listener socket
    def __init__(self, host=socket.gethostbyname(socket.gethostname()), port=8089):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s :: %(levelname)8s :: %(name)s :: %(filename)s:%(lineno)-3s :: %(funcName)-20s() :: %(message)s')
        logging.info('initializing %s:%s' % (host, port))

        self._peers = set()

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((host, port))
        self._serverSocket.listen(3)
        self._thisPeer = (host, port)

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
        connection.close()

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

    # TODO use getaddrinfo
    # TODO use hton etc to save bytes

    def joinNetwork(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('joining network through %s:%s' % (host, port))
        unvisitedPeers = {(host, port)}
        while len(unvisitedPeers):
            iterationPeers = set()  # other peers discovered from peer list of unvisited nodes
            for newHost, newPort in unvisitedPeers:
                # TODO set timeout
                try:
                    self.sendConnect(newHost, newPort)
                    newPeers = self.sendPeersRequest(newHost, newPort)
                except:
                    self._logger.info('failed to connect or get peers from %s:%s' % (newHost, newPort))
                    pass
                else:
                    iterationPeers.update(newPeers)
            unvisitedPeers.clear()
            unvisitedPeers.update(iterationPeers - self._peers - {self._thisPeer})

    # connect to a single node i.e. request host:port node adds self to its peer list
    def sendConnect(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('connecting to %s:%s' % (host, port))
        # TODO consider not using .value
        buffer = Node.DELIM.join(map(str, (Node.MessageType.CONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()
        self._peers.add((host, port))

    # connect to a single node i.e. request host:port node adds self to its peer list
    def sendDisconnect(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('disconnecting from %s:%s' % (host, port))
        buffer = Node.DELIM.join(map(str, (Node.MessageType.DISCONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()
        self._peers.remove((host, port))

    # TODO consider len based messages over delim based
    def sendPeersRequest(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('requesting peers from %s:%s' % (host, port))
        buffer = str(Node.MessageType.PEERS_REQUEST.value) + Node.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        recvBuffer = ''
        # TODO consider len based messages over delim based, searching str each time not efficient
        while Node.DELIM not in recvBuffer:
            recvBuffer += clientSocket.recv(4096).decode()
            self._logger.debug('received %s, len %s' % (recvBuffer, len(recvBuffer)))
        clientSocket.close()
        peerList = eval(recvBuffer.split(Node.DELIM)[0])
        return peerList

