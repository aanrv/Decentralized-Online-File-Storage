# storagenode.py

from common import *    # RequestType, Fields, RequestFields
from node import Node
import os
import socket
import hashlib
from enum import Enum
import tempfile

class StorageNode(Node):

    def __init__(self, dataDir, host=socket.gethostbyname(socket.gethostname()), port=8089):
        super().__init__(host, port)

        self._handlers.update({
            RequestType.DATA_ADD    : self._handleDataAdd,
            RequestType.DATA_GET    : self._handleDataGet,
            RequestType.DATA_REMOVE : self._handleDataRemove,
        })

        self._dataDir = os.path.expandvars(dataDir)
        os.makedirs(self._dataDir, exist_ok=True)

    def sendDataAdd(self, host, port, filename):
        filename = os.path.expandvars(filename)
        self._logger.info('sending data add to %s:%s' % (host, port))
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        dataSize = os.path.getsize(filename)
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_ADD.value, dataSize))) + StorageNode.DELIM
        bytesRemaining = dataSize
        clientSocket.send(buffer.encode())
        with open(filename, 'rb') as f:
            while bytesRemaining:
                assert(bytesRemaining > 0)
                data = f.read(4096)
                clientSocket.send(data)
                bytesRemaining -= len(data)
        clientSocket.close()

    def sendDataGet(self, host, port, datahash, targetfile=None):
        if not targetfile:
            targetfile=os.path.join(self._dataDir, datahash)
        targetfile = os.path.expandvars(targetfile)
        self._logger.info('requesting data from %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_GET.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        self._logger.info('receiving')
        # keep recv'ing until data size can be parsed
        DELIM_ENCODED = Node.DELIM.encode()
        recvBuffer = clientSocket.recv(4096)
        while (recvBuffer.count(DELIM_ENCODED) <= 0):
            recvBuffer += clientSocket.recv(4096)
        dataSize = int(recvBuffer.split(DELIM_ENCODED)[0].decode())
        data = int(recvBuffer.split(DELIM_ENCODED)[1])
        tmp = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        totalBytesWritten = 0
        totalBytesWritten += tmp.write(data)
        # keep reading until dataSize bytes are read
        while (totalBytesWritten < dataSize):
            data = clientSocket.recv(4096)
            totalBytesWritten += tmp.write(data)
        assert(totalBytesWritten == dataSize)
        os.rename(tmp.name, targetfile)
        tmp.close()
        clientSocket.close()

    def sendDataRemove(self, host, port, datahash):
        self._logger.info('sending data remove to %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_REMOVE.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()

    def _handleDataAdd(self, buffer, connection):
        # keep reading until able to parse data size
        # will almost always only run once
        DELIM_ENCODED = Node.DELIM.encode()
        while (buffer.count(DELIM_ENCODED) <= Fields[RequestType.DATA_ADD].SIZE.value):
            buffer += connection.recv(4096)
        dataSize = int(buffer.split(DELIM_ENCODED)[Fields[RequestType.DATA_ADD].SIZE.value].decode())
        # get data currently in buffer
        data = buffer.split(DELIM_ENCODED)[Fields[RequestType.DATA_ADD].DATA.value]
        # write to temporary file
        tmp = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        totalBytesWritten = 0
        totalBytesWritten += tmp.write(data)
        # datahash will be output filename
        datahash = hashlib.sha256()
        datahash.update(data)
        # while dataSize bytes not written, keep recv'ing and writing
        while (totalBytesWritten < dataSize):
            data = connection.recv(4096)
            totalBytesWritten += tmp.write(data)
            datahash.update(data)
        print('WRITTEN %s SIZE %s' % (totalBytesWritten, dataSize))
        outfilename = os.path.join(self._dataDir, datahash.hexdigest())
        os.rename(tmp.name, outfilename)
        tmp.close()
        assert(totalBytesWritten == dataSize)

    def _handleDataGet(self, buffer, connection):
        buffer = buffer.decode()
        while (buffer.count(Node.DELIM) != len(Fields[RequestType.DATA_GET])):
            buffer += connection.recv(4096).decode()
        filename = buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_GET].HASH.value]
        fullfile = os.path.join(self._dataDir, filename)
        bytesRemaining = os.path.getsize(fullfile)
        outbuffer = str(bytesRemaining) + StorageNode.DELIM
        connection.send(outbuffer.encode())
        with open(fullfile, 'rb') as f:
            while bytesRemaining:
                data = f.read(4096)
                connection.send(data)
                bytesRemaining -= len(data)
                assert(bytesRemaining >= 0)
            assert(bytesRemaining == 0)

    def _handleDataRemove(self, buffer, connection):
        buffer = buffer.decode()
        while (buffer.count(Node.DELIM) != len(Fields[RequestType.DATA_REMOVE])):
            buffer += connection.recv(4096).decode()
        filename = buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_REMOVE].HASH.value]
        os.remove(os.path.join(self._dataDir, filename))

