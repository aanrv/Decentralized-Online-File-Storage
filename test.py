#!/usr/bin/env python

from storagenode import *
from time import sleep
import hashlib
import os

def main():
    storagedir = '$PWD/data/'
    a = StorageNode(storagedir)
    b = StorageNode(storagedir, port=8090)
    c = StorageNode(storagedir, port=8091)
    d = StorageNode(storagedir, port=8092)
    e = StorageNode(storagedir, port=8093)

    b.sendConnect('127.0.1.1', 8089)
    sleep(1)
    assert(a._peers == {b._thisPeer})
    assert(b._peers == {a._thisPeer})
    c.joinNetwork('127.0.1.1', 8090)
    sleep(1)
    assert(a._peers == {b._thisPeer, c._thisPeer})
    assert(b._peers == {a._thisPeer, c._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer})
    b.sendDisconnect('127.0.1.1', 8089)
    sleep(1)
    assert(a._peers == {c._thisPeer})
    assert(b._peers == {c._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer})
    d.joinNetwork('127.0.1.1', 8090)
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
    e.joinNetwork('127.0.1.1', 8091)
    sleep(1)
    assert(e._peers == {c._thisPeer})
    assert(c._peers == {e._thisPeer})
    e.sendConnect('127.0.1.1', 8089)
    sleep(1)
    assert(e._peers == {a._thisPeer, c._thisPeer})
    assert(a._peers == {d._thisPeer, e._thisPeer})
    c.joinNetwork('127.0.1.1', 8093)
    assert(a._peers == {c._thisPeer, d._thisPeer, e._thisPeer})
    assert(b._peers == {c._thisPeer, d._thisPeer})
    assert(c._peers == {a._thisPeer, b._thisPeer, d._thisPeer, e._thisPeer})
    assert(d._peers == {a._thisPeer, b._thisPeer, c._thisPeer})
    assert(e._peers == {a._thisPeer, c._thisPeer})
    sleep(1)
    datastr = 'Hello, World!'
    filename = hashlib.sha256(datastr.encode()).hexdigest()
    fullfile = os.path.expandvars(os.path.join(storagedir, filename))
    a.sendDataAdd('127.0.1.1', 8091, datastr)
    sleep(1)
    assert(os.path.isfile(fullfile))
    with open(fullfile, 'r') as f:
        assert(datastr == f.read())
    recvdata = a.sendDataGet('127.0.1.1', 8091, filename)
    assert(recvdata == datastr)
    a.sendDataRemove('127.0.1.1', 8091, filename)
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

