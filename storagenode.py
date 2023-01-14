# storagenode.py

from common import *    # RequestType and *RequestFields types
from node import Node
import os
import socket
import hashlib
from enum import Enum

class StorageNode(Node):

    def __init__(self, dataDir, host=socket.gethostbyname(socket.gethostname()), port=8089):
        super().__init__(host, port)

        self._handlers.update({
            RequestType.DATA_ADD    : self._handleDataAdd,
            RequestType.DATA_GET    : self._handleDataGet,
            RequestType.DATA_REMOVE : self._handleDataRemove,
        })

        self._dataDir = os.path.expandvars(dataDir)
        if not os.path.exists(self._dataDir):
            self._logger.info('creating dir %s' % self._dataDir)
            os.makedirs(self._dataDir)

    def sendDataAdd(self, host, port, data):
        # TODO remove and handle large files
        assert(len(data) < 4000)
        self._logger.info('sending data add to %s:%s' % (host, port))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_ADD.value, str(len(data)), data))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()

    def sendDataGet(self, host, port, datahash):
        self._logger.info('requesting data from %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_GET.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        self._logger.info('receiving')
        data = clientSocket.recv(4096).decode()
        data = data.split(Node.DELIM)[0]
        clientSocket.close()
        return data

    def sendDataRemove(self, host, port, datahash):
        self._logger.info('sending data remove to %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_REMOVE.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()

    def _handleDataAdd(self, buffer, _):
        buffer = buffer.decode()
        _, dataSize, data = buffer.split(StorageNode.DELIM)[:-1]
        filename = hashlib.sha256(data.encode()).hexdigest()
        with open(os.path.join(self._dataDir, filename), 'w') as f:
            f.write(data)

    def _handleDataGet(self, buffer, connection):
        buffer = buffer.decode()
        filename = buffer.split(StorageNode.DELIM)[DataGetRequestFields.HASH.value]
        with open(os.path.join(self._dataDir, filename), 'r') as f:
            data = f.read()
        buffer = data + StorageNode.DELIM
        connection.send(buffer.encode())

    def _handleDataRemove(self, buffer, _):
        buffer = buffer.decode()
        filename = buffer.split(StorageNode.DELIM)[DataRemoveRequestFields.HASH.value]
        os.remove(os.path.join(self._dataDir, filename))

