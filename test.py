#!/usr/bin/env python

from storagenode import *
from time import sleep
import hashlib
import os

def main():
    storagedir = '$PWD/data/'
    testfile = '$PWD/filetest/enc.file'
    baseport = 8089
    a = StorageNode(storagedir, port=baseport)
    b = StorageNode(storagedir, port=baseport+1)
    c = StorageNode(storagedir, port=baseport+2)
    d = StorageNode(storagedir, port=baseport+3)
    e = StorageNode(storagedir, port=baseport+4)

    b.sendConnect('127.0.1.1', baseport)
    sleep(1)
    assert(a._peers == {b._thisPeer})
    assert(b._peers == {a._thisPeer})
    c.joinNetwork('127.0.1.1', baseport+1)
    sleep(1)
    assert(a._peers == {b._thisPeer, c._thisPeer})
    assert(b._peers == {a._thisPeer, c._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer})
    b.sendDisconnect('127.0.1.1', baseport)
    sleep(1)
    assert(a._peers == {c._thisPeer})
    assert(b._peers == {c._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer})
    d.joinNetwork('127.0.1.1', baseport+1)
    sleep(1)
    assert(a._peers == {c._thisPeer, d._thisPeer})
    assert(b._peers == {c._thisPeer, d._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer, d._thisPeer})
    assert(d._peers == {a._thisPeer, b._thisPeer, c._thisPeer})
    c.leaveNetwork()
    sleep(1)
    assert(a._peers == {d._thisPeer})
    assert(b._peers == {d._thisPeer})
    assert(not c._peers)
    assert(d._peers == {a._thisPeer, b._thisPeer})
    e.joinNetwork('127.0.1.1', baseport+2)
    sleep(1)
    assert(e._peers == {c._thisPeer})
    assert(c._peers == {e._thisPeer})
    e.sendConnect('127.0.1.1', baseport)
    sleep(1)
    assert(e._peers == {a._thisPeer, c._thisPeer})
    assert(a._peers == {d._thisPeer, e._thisPeer})
    c.joinNetwork('127.0.1.1', baseport+4)
    assert(a._peers == {c._thisPeer, d._thisPeer, e._thisPeer})
    assert(b._peers == {c._thisPeer, d._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer, d._thisPeer, e._thisPeer})
    assert(d._peers == {a._thisPeer, b._thisPeer, c._thisPeer})
    assert(e._peers == {a._thisPeer, c._thisPeer})
    sleep(1)
    filename = hashlib.sha256(open(os.path.expandvars(testfile), 'rb').read()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(storagedir, filename))
    a.sendDataAdd('127.0.1.1', baseport+2, filename=testfile)
    sleep(1)
    assert(os.path.isfile(fullfile))
    assert(open(os.path.expandvars(testfile), 'rb').read() == open(fullfile, 'rb').read())
    a.sendDataRemove('127.0.1.1', baseport+2, filename)
    sleep(1)
    assert(not os.path.isfile(fullfile))

    a.shutdown()
    b.shutdown()
    c.shutdown()
    d.shutdown()
    e.shutdown()
    e.shutdown()

    print('Sucess!')

main()

