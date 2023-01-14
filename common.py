# common.py

from enum import Enum

# possible request message types sent by local host to a remote host
RequestType = Enum('RequestType', [
    'PING',         # a socket connect and disconnect
    'CONNECT',      # request to connect i.e. add one another to peers lists
    'DISCONNECT',   # request to remove one another from peers list
    'GET_PEERS',    # request remote host's peers list
    'DATA_ADD',     # request remote host to add provided data to its storage directory
    'DATA_GET',     # request data with the provided hash
    'DATA_REMOVE',  # request remote host to remove data with the provided hash from its storage directory
])

Fields = {
        RequestType.PING        : Enum('PingFields',        ['TYPE'],                   start=0),
        RequestType.CONNECT     : Enum('ConnectFields',     ['TYPE', 'HOST', 'PORT'],   start=0),
        RequestType.DISCONNECT  : Enum('DisconnectFields',  ['TYPE', 'HOST', 'PORT'],   start=0),
        RequestType.GET_PEERS   : Enum('GetPeersFields',    ['TYPE'],                   start=0),
        RequestType.DATA_ADD    : Enum('DataAddFields',     ['TYPE', 'SIZE', 'DATA'],   start=0),
        RequestType.DATA_GET    : Enum('DataGetFields',     ['TYPE', 'HASH'],           start=0),
        RequestType.DATA_REMOVE : Enum('DataRemoveFields',  ['TYPE', 'HASH'],           start=0),
}

# request message field indices when split by delim
# starts with 1 because 0 is always the message type

RequestTypeIndex = 0


