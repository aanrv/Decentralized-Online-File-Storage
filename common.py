# common.py

from enum import Enum

RequestType = Enum('RequestType', [
    'PING',
    'CONNECT',
    'DISCONNECT',
    'GET_PEERS',
    'DATA_ADD',
    'DATA_GET',
    'DATA_REMOVE',
])

