#!/usr/bin/env python

from storagenode import *
from time import sleep
import hashlib
import os

def main():
    storagedir = '$PWD/data/'
    testfile = '$PWD/filetest/enc.file'
    baseport = 8080
    a = StorageNode(os.path.join(storagedir, str(baseport)), port=baseport)
    b = StorageNode(os.path.join(storagedir, str(baseport+1)), port=baseport+1)
    c = StorageNode(os.path.join(storagedir, str(baseport+2)), port=baseport+2)
    d = StorageNode(os.path.join(storagedir, str(baseport+3)), port=baseport+3)
    e = StorageNode(os.path.join(storagedir, str(baseport+4)), port=baseport+4)

    b.sendConnect('127.0.1.1', baseport)
    sleep(1)
    assert(a.peers == {b._thisPeer})
    assert(b.peers == {a._thisPeer})
    c.joinNetwork('127.0.1.1', baseport+1)
    sleep(1)
    assert(a.peers == {b._thisPeer, c._thisPeer})
    assert(b.peers == {a._thisPeer, c._thisPeer})
    assert(c.peers == {a._thisPeer, b._thisPeer})
    b.sendDisconnect('127.0.1.1', baseport)
    sleep(1)
    assert(a.peers == {c._thisPeer})
    assert(b.peers == {c._thisPeer})
    assert(c.peers == {a._thisPeer, b._thisPeer})
    d.joinNetwork('127.0.1.1', baseport+1)
    sleep(1)
    assert(a.peers == {c._thisPeer, d._thisPeer})
    assert(b.peers == {c._thisPeer, d._thisPeer})
    assert(c.peers == {a._thisPeer, b._thisPeer, d._thisPeer})
    assert(d.peers == {a._thisPeer, b._thisPeer, c._thisPeer})
    c.leaveNetwork()
    sleep(1)
    assert(a.peers == {d._thisPeer})
    assert(b.peers == {d._thisPeer})
    assert(not c.peers)
    assert(d.peers == {a._thisPeer, b._thisPeer})
    e.joinNetwork('127.0.1.1', baseport+2)
    sleep(1)
    assert(e.peers == {c._thisPeer})
    assert(c.peers == {e._thisPeer})
    e.sendConnect('127.0.1.1', baseport)
    sleep(1)
    assert(e.peers == {a._thisPeer, c._thisPeer})
    assert(a.peers == {d._thisPeer, e._thisPeer})
    c.joinNetwork('127.0.1.1', baseport+4)
    assert(a.peers == {c._thisPeer, d._thisPeer, e._thisPeer})
    assert(b.peers == {c._thisPeer, d._thisPeer})
    assert(c.peers == {a._thisPeer, b._thisPeer, d._thisPeer, e._thisPeer})
    assert(d.peers == {a._thisPeer, b._thisPeer, c._thisPeer})
    assert(e.peers == {a._thisPeer, c._thisPeer})
    sleep(1)

    filename = hashlib.sha256(open(os.path.expandvars(testfile), 'rb').read()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(c.dataDir, filename))
    recvfile = fullfile+'.recv'
    a.sendDataAdd('127.0.1.1', baseport+2, filename=testfile)
    sleep(1)
    assert(os.path.isfile(fullfile))
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(fullfile, 'rb').read())
    a.sendDataGet('127.0.1.1', baseport+2, filename, recvfile)
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(recvfile, 'rb').read())
    os.remove(recvfile)
    a.sendDataRemove('127.0.1.1', baseport+2, filename)
    sleep(1)
    assert(not os.path.isfile(fullfile))

    filename = hashlib.sha256(open(os.path.expandvars(testfile), 'rb').read()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(c.dataDir, filename))
    recvfile = fullfile+'.recv'
    a.sendDataAdd('127.0.1.1', baseport+2, bytedata=open(os.path.expandvars(testfile), 'rb').read())
    sleep(1)
    assert(os.path.isfile(fullfile))
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(fullfile, 'rb').read())
    a.sendDataGet('127.0.1.1', baseport+2, filename, recvfile)
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(recvfile, 'rb').read())
    os.remove(recvfile)
    a.sendDataRemove('127.0.1.1', baseport+2, filename)
    sleep(1)
    assert(not os.path.isfile(fullfile))

    a.sendDataGet('127.0.1.1', baseport+2, 'fdjgfnjds', recvfile)

    print('---------------------------------------------------')
    a.uploadFile(testfile)
    sleep(3)
    a.downloadFile(os.path.basename(testfile), recvfile)
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

