# node.py

from common import *    # RequestType, Fields, RequestTypeIndex
import sys
import socket
from time import sleep
import logging
from threading import Thread
from enum import Enum

class Node:

    DELIM = '\1'

    # initialize listener socket
    def __init__(self, host=socket.gethostbyname(socket.gethostname()), port=8089):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s :: %(levelname)8s :: %(name)s :: %(filename)14s:%(lineno)-3s :: %(funcName)-20s() :: %(message)s')
        logging.info('initializing %s:%s' % (host, port))

        self._thisPeer = (host, port)
        self._peers = set()

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((host, port))
        self._serverSocket.listen(3)
        self._logger = logging.getLogger('%s' % str(self._serverSocket.getsockname()))
        self._logger.info('initialized socket')

        # start server thread
        self._handleIncomingContinue = True
        self._serverThread = Thread(target=self.handleIncoming)
        self._serverThread.start()

        self._handlers = {
            RequestType.PING       : self._handlePing,
            RequestType.CONNECT    : self._handleConnect,
            RequestType.DISCONNECT : self._handleDisconnect,
            RequestType.GET_PEERS  : self._handleGetPeers,
        }

    def __del__(self):
        self.shutdown()

    # TODO use getaddrinfo
    # TODO use hton etc to save bytes

    def shutdown(self):
        self._logger.info('shutting down node')
        if not self._handleIncomingContinue:
            self._logger.info('already shutdown, nothing to do')
            return
        self._handleIncomingContinue = False
        sleep(1)
        try:
            self.sendPing(*self._thisPeer)  # a hack to move the loop forward in case no other nodes are connecting
        except:
            pass
        self._serverThread.join()
        self._serverSocket.close()
        self._logger.info('shutdown complete')

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
                    newPeers = self.sendGetPeers(newHost, newPort)
                except:
                    self._logger.info('failed to connect or get peers from %s:%s' % (newHost, newPort))
                    pass
                else:
                    iterationPeers.update(newPeers)
            unvisitedPeers.clear()
            unvisitedPeers.update(iterationPeers - self._peers - {self._thisPeer})

    def leaveNetwork(self):
        self._logger.info('leaving network')
        for targetNode in list(self._peers):
            self.sendDisconnect(*targetNode)

    def sendPing(self, host, port):
        buffer = str(RequestType.PING.value) + Node.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()

    # connect to a single node i.e. request host:port node adds self to its peer list
    def sendConnect(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('connecting to %s:%s' % (host, port))
        # TODO consider not using .value
        buffer = Node.DELIM.join(map(str, (RequestType.CONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()
        # TODO mutex for self._peers
        self._peers.add((host, port))

    # connect to a single node i.e. request host:port node adds self to its peer list
    def sendDisconnect(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('disconnecting from %s:%s' % (host, port))
        buffer = Node.DELIM.join(map(str, (RequestType.DISCONNECT.value, *self._serverSocket.getsockname()))) + Node.DELIM
        self._logger.debug('sending buffer: %s' % buffer)
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()
        try:
            self._peers.remove((host, port))
        except KeyError:
            self._logger.info('%s:%s not in peers list, nothing to remove' % (host, port))

    # TODO consider len based messages over delim based
    def sendGetPeers(self, host, port):
        if ((host, port) == self._thisPeer):
            raise Exception('attempted to contact self host')
        self._logger.info('requesting peers from %s:%s' % (host, port))
        buffer = str(RequestType.GET_PEERS.value) + Node.DELIM
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

    def handleIncoming(self):
        while self._handleIncomingContinue:
            self._handleIncoming()

    def _handlePing(self, *_):
        self._logger.info('received ping')

    def _handleIncoming(self):
        connection, address = self._serverSocket.accept()
        self._logger.info('accepted %s' % str(address))
        # TODO create thread per connection
        # TODO make messages more robust and consistent e.g. sizes to expect etc
        buffer = connection.recv(4096)
        self._logger.info('received buffer')
        headbuffer = buffer[:len(str(len(RequestType))) + 1].decode()   # to decode only portion needed for determining message type
        incomingRequestType = RequestType(int(headbuffer.split(Node.DELIM)[RequestTypeIndex]))
        self._logger.info('received incoming request %s' % incomingRequestType)
        self._handlers[incomingRequestType](buffer, connection)
        connection.close()

    def _handleConnect(self, buffer, _):
        buffer = buffer.decode()
        host = buffer.split(Node.DELIM)[Fields[RequestType.CONNECT].HOST.value]
        port = int(buffer.split(Node.DELIM)[Fields[RequestType.CONNECT].PORT.value])
        self._peers.add((host, port))
        self._logger.info('received connect from %s:%s' % (host, port))

    def _handleDisconnect(self, buffer, _):
        buffer = buffer.decode()
        host = buffer.split(Node.DELIM)[Fields[RequestType.DISCONNECT].HOST.value]
        port = int(buffer.split(Node.DELIM)[Fields[RequestType.DISCONNECT].PORT.value])
        try:
            self._peers.remove((host, port))
        except KeyError:
            self._logger.info('%s:%s not in peers list, nothing to remove' % (host, port))
        self._logger.info('recieved disconnect from %s:%s' % (host, port))

    def _handleGetPeers(self, _, connection):
        buffer = repr(self._peers) + Node.DELIM
        connection.send(buffer.encode())

