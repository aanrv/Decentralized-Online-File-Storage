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

# request message field indices when split by delim
# starts with 1 because 0 is always the message type

ConnectRequestFields = Enum('ConnectFields', [
    'HOST',
    'PORT',
])

DisconnectRequestFields = Enum('DisconnectFields', [
    'HOST',
    'PORT',
])

DataAddRequestFields = Enum('DataAddFields', [
    'SIZE',
    'DATA',
])

DataGetRequestFields = Enum('DataGetFields', [
    'HASH',
])

DataRemoveRequestFields = Enum('DataRemoveFields', [
    'HASH',
])

