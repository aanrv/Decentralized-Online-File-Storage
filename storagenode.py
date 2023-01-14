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
        if not os.path.exists(self._dataDir):
            self._logger.info('creating dir %s' % self._dataDir)
            os.makedirs(self._dataDir)

    def sendDataAdd(self, host, port, data='', filename=''):
        self._logger.info('sending data add to %s:%s' % (host, port))
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        if data:
            buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_ADD.value, str(len(data)), data)))
            clientSocket.send(buffer.encode())
        else:
            dataSize = os.path.getsize(filename)
            buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_ADD.value, dataSize))) + StorageNode.DELIM
            bytesRemaining = dataSize
            clientSocket.send(buffer.encode())
            with open(filename, 'r') as f:
                while bytesRemaining:
                    print('bytes remaining %s' % bytesRemaining)
                    assert(bytesRemaining > 0)
                    data = f.read(4096)
                    clientSocket.send(data.encode())
                    bytesRemaining -= len(data)
        clientSocket.close()

    def sendDataGet(self, host, port, datahash):
        self._logger.info('requesting data from %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_GET.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        self._logger.info('receiving')
        # keep recv'ing until data size can be parsed
        recvBuffer = clientSocket.recv(4096).decode()
        while (recvBuffer.count(StorageNode.DELIM) < 1):
            recvBuffer += clientSocket.recv(4096).decode()
        dataSize = int(recvBuffer.split(Node.DELIM)[0])
        data = recvBuffer.split(StorageNode.DELIM)[1]
        # keep reading until dataSize bytes are read
        while (len(data) < dataSize):
            data += clientSocket.recv(4096).decode()
        clientSocket.close()
        return data

    def sendDataRemove(self, host, port, datahash):
        self._logger.info('sending data remove to %s:%s (%s)' % (host, port, datahash))
        buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_REMOVE.value, datahash))) + StorageNode.DELIM
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        clientSocket.send(buffer.encode())
        clientSocket.close()

    def _handleDataAdd(self, buffer, connection):
        buffer = buffer.decode()
        # TODO reads entire data into memory, not feasible for very large files, handle
        # TODO handle binary files
        # recv until can get dataSize
        while (buffer.count(Node.DELIM) <= Fields[RequestType.DATA_ADD].SIZE.value):
            buffer += connection.recv(4096).decode()
        dataSize = int(buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_ADD].SIZE.value])
        # get data currently in buffer
        data = buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_ADD].DATA.value]
        # write to temporary file
        tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        totalBytesWritten = 0
        totalBytesWritten += tmp.write(data)
        # datahash will be output filename
        datahash = hashlib.sha256()
        datahash.update(data.encode())
        # while dataSize bytes not written, keep recv'ing and writing
        while (totalBytesWritten < dataSize):
            data = connection.recv(4096).decode()
            totalBytesWritten += tmp.write(data)
            datahash.update(data.encode())
        assert(totalBytesWritten == dataSize)
        outfilename = os.path.join(self._dataDir, datahash.hexdigest())
        os.rename(tmp.name, outfilename)
        tmp.close()

    def _handleDataGet(self, buffer, connection):
        buffer = buffer.decode()
        while (buffer.count(Node.DELIM) != len(Fields[RequestType.DATA_GET])):
            buffer += connection.recv(4096).decode()
        filename = buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_GET].HASH.value]
        with open(os.path.join(self._dataDir, filename), 'r') as f:
            data = f.read()
        buffer = StorageNode.DELIM.join([str(len(data)), data]) # no ending delim needed since size field is provided
        connection.send(buffer.encode())

    def _handleDataRemove(self, buffer, connection):
        buffer = buffer.decode()
        while (buffer.count(Node.DELIM) != len(Fields[RequestType.DATA_REMOVE])):
            buffer += connection.recv(4096).decode()
        filename = buffer.split(StorageNode.DELIM)[Fields[RequestType.DATA_REMOVE].HASH.value]
        os.remove(os.path.join(self._dataDir, filename))

