# storagenode.py

from common import *    # RequestType, Fields, RequestFields
from node import Node
import os
import socket
import hashlib
from enum import Enum
import tempfile
import random

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

        self._filePartsLoader = os.path.join(self._dataDir, '.filePartsLoader')
        if not os.path.isfile(self._filePartsLoader):
            with open(self._filePartsLoader, 'w+') as f:
                f.write(repr(dict()))
        self._fileParts = eval(open(self._filePartsLoader, 'r').read())
        self._logger.info('dataDir %s filePartsLoader %s' % (self._dataDir, self._filePartsLoader))

    def uploadFile(self, filename):
        filename = os.path.expandvars(filename)
        self._logger.info('uploading file %s' % filename)
        partSize = 7000
        parts = list()
        with open(filename, 'rb') as f:
            while True:
                buffer = f.read(partSize)
                if not buffer:
                    break

                for host, port in self._chooseNode():
                    self._logger.debug('sending part to %s:%s' % (host, port))
                    self.sendDataAdd(host, port, bytedata=buffer)

                filehash = hashlib.sha256(buffer).hexdigest()
                self._logger.debug('sent %s' % filehash)
                parts.append(filehash)

        basename = os.path.basename(filename)
        self._fileParts[basename] = parts
        open(self._filePartsLoader, 'w').write(repr(self._fileParts))
        self._logger.info('done uploading file %s' % filename)

    def downloadFile(self, basename, outfile):
        self._logger.info('downloading %s' % basename)
        partsfound = dict()
        # go by host
        for host, port in self._peers:
            # get all files you can from host
            for partHash in set(self._fileParts[basename]) - set(partsfound.keys()):
                self._logger.debug('requesting %s from %s:%s' % (partHash, host, port))
                recvfile = self.sendDataGet(host, port, partHash)
                if recvfile:
                    partsfound[partHash] = recvfile
                    self._logger.info('found %s' % partHash)

        # confirm all files were found
        if (len(partsfound) != len(self._fileParts[basename])):
            self._logger.info('unable to find all file parts')
        else:
            # write files sequentially to outfile
            outfile = os.path.expandvars(outfile)
            with open(outfile, 'w+b') as f:
                self._logger.info('writing parts to %s' % outfile)
                for partHash in self._fileParts[basename]:
                    f.write(open(partsfound[partHash], 'rb').read())
        # remove downloaded parts
        for _, filename in partsfound.items():
            self._logger.debug('removing %s' % filename)
            os.remove(filename)

    def removeFile(self, basename):
        self._logger.info('removing file %s from network' % basename)
        for filehash in self._fileParts[basename]:
            list(map(lambda hp: self.sendDataRemove(hp[0], hp[1], filehash), self._peers))
        self._fileParts.pop(basename, None)

    def _chooseNode(self):
        return random.sample(self._peers, 3)

    def sendDataAdd(self, host, port, filename='', bytedata=''):
        self._logger.info('sending data add to %s:%s' % (host, port))
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        if filename:
            filename = os.path.expandvars(filename)
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
        elif bytedata:
            buffer = StorageNode.DELIM.join(map(str, (RequestType.DATA_ADD.value, len(bytedata)))) + StorageNode.DELIM
            buffer = buffer.encode()
            buffer += bytedata
            clientSocket.send(buffer)
        else:
            assert(False)
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
        if (dataSize == 0):
            self._logger.debug('node does not have data')
            return None
        # have to join after split in case has buffer has DELIM_ENCODED as a byte value
        data = DELIM_ENCODED.join(recvBuffer.split(DELIM_ENCODED)[1:])
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
        return targetfile

    def sendDataRemove(self, host, port, datahash):
        self._logger.info('sending data remove to %s:%s for %s' % (host, port, datahash))
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
        # have to join after split in case has buffer has DELIM_ENCODED as a byte value
        data = DELIM_ENCODED.join(buffer.split(DELIM_ENCODED)[Fields[RequestType.DATA_ADD].DATA.value:])
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
        if not os.path.isfile(fullfile):
            self._logger.info('failed to find file %s' % fullfile)
            outbuffer = '0' + StorageNode.DELIM
            connection.send(outbuffer.encode())
            return
        self._logger.info('found file %s' % fullfile)
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
        self._logger.info('removing %s' % filename)
        try:
            os.remove(os.path.join(self._dataDir, filename))
        except FileNotFoundError:
            self._logger.info('nothing to remove')

    @property
    def peers(self):
        return self._peers

    @property
    def dataDir(self):
        return self._dataDir

    @property
    def filePartsLoader(self):
        return self._filePartsLoder

    def storedData(self):
        return list(filter(os.path.isfile, os.listdir(self._dataDir)))

