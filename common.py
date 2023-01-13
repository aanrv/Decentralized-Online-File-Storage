# common.py

from enum import Enum

RequestType = Enum('RequestType', [
    'CONNECT',
    'DISCONNECT',
    'PEERS_LIST',
    'DATA_ADD',
    'DATA_GET',
    'DATA_REMOVE',
])

