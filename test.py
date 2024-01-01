#!/usr/bin/env python

from storagenode import *
from time import sleep
import hashlib
import os
import socket

def main():
    storagedir = '$PWD/data/'
    testfile = '$PWD/filetest/order-book'
    host = socket.gethostbyname(socket.gethostname())
    baseport = 8095
    a = StorageNode(os.path.join(storagedir, str(baseport)), port=baseport)
    b = StorageNode(os.path.join(storagedir, str(baseport+1)), port=baseport+1)
    c = StorageNode(os.path.join(storagedir, str(baseport+2)), port=baseport+2)
    d = StorageNode(os.path.join(storagedir, str(baseport+3)), port=baseport+3)
    e = StorageNode(os.path.join(storagedir, str(baseport+4)), port=baseport+4)

    b.sendConnect(host, baseport)
    sleep(1)
    assert(a.peers == {b.thisPeer})
    assert(b.peers == {a.thisPeer})
    c.joinNetwork(host, baseport+1)
    sleep(1)
    assert(a.peers == {b.thisPeer, c.thisPeer})
    assert(b.peers == {a.thisPeer, c.thisPeer})
    assert(c.peers == {a.thisPeer, b.thisPeer})
    b.sendDisconnect(host, baseport)
    sleep(1)
    assert(a.peers == {c.thisPeer})
    assert(b.peers == {c.thisPeer})
    assert(c.peers == {a.thisPeer, b.thisPeer})
    d.joinNetwork(host, baseport+1)
    sleep(1)
    assert(a.peers == {c.thisPeer, d.thisPeer})
    assert(b.peers == {c.thisPeer, d.thisPeer})
    assert(c.peers == {a.thisPeer, b.thisPeer, d.thisPeer})
    assert(d.peers == {a.thisPeer, b.thisPeer, c.thisPeer})
    c.leaveNetwork()
    sleep(1)
    assert(a.peers == {d.thisPeer})
    assert(b.peers == {d.thisPeer})
    assert(not c.peers)
    assert(d.peers == {a.thisPeer, b.thisPeer})
    e.joinNetwork(host, baseport+2)
    sleep(1)
    assert(e.peers == {c.thisPeer})
    assert(c.peers == {e.thisPeer})
    e.sendConnect(host, baseport)
    sleep(1)
    assert(e.peers == {a.thisPeer, c.thisPeer})
    assert(a.peers == {d.thisPeer, e.thisPeer})
    c.joinNetwork(host, baseport+4)
    assert(a.peers == {c.thisPeer, d.thisPeer, e.thisPeer})
    assert(b.peers == {c.thisPeer, d.thisPeer})
    assert(c.peers == {a.thisPeer, b.thisPeer, d.thisPeer, e.thisPeer})
    assert(d.peers == {a.thisPeer, b.thisPeer, c.thisPeer})
    assert(e.peers == {a.thisPeer, c.thisPeer})
    sleep(1)

    filename = hashlib.sha256(open(os.path.expandvars(testfile), 'rb').read()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(c.dataDir, filename))
    recvfile = fullfile+'.recv'
    a.sendDataAdd(host, baseport+2, filename=testfile)
    sleep(1)
    assert(os.path.isfile(fullfile))
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(fullfile, 'rb').read())
    a.sendDataGet(host, baseport+2, filename, recvfile)
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(recvfile, 'rb').read())
    os.remove(recvfile)
    a.sendDataRemove(host, baseport+2, filename)
    sleep(1)
    assert(not os.path.isfile(fullfile))

    filename = hashlib.sha256(open(os.path.expandvars(testfile), 'rb').read()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(c.dataDir, filename))
    recvfile = fullfile+'.recv'
    a.sendDataAdd(host, baseport+2, bytedata=open(os.path.expandvars(testfile), 'rb').read())
    sleep(1)
    assert(os.path.isfile(fullfile))
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(fullfile, 'rb').read())
    a.sendDataGet(host, baseport+2, filename, recvfile)
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(recvfile, 'rb').read())
    os.remove(recvfile)
    a.sendDataRemove(host, baseport+2, filename)
    sleep(1)
    assert(not os.path.isfile(fullfile))

    a.sendDataGet(host, baseport+2, 'fdjgfnjds', recvfile)

    print('---------------------------------------------------')
    recvfile = os.path.expandvars(os.path.join(a.dataDir, filename) + '.recv')
    a.uploadFile(testfile, encrypt=True)
    sleep(3)
    a.downloadFile(os.path.basename(testfile), recvfile, decrypt=True)
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(os.path.expandvars(recvfile), 'rb').read())
    os.remove(recvfile)
    sleep(3)
    a.removeFile(os.path.basename(testfile))

    a.shutdown()
    b.shutdown()
    c.shutdown()
    d.shutdown()
    e.shutdown()
    e.shutdown()

    print('Tests passed')

main()

