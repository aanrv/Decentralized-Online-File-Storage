# Decentralized-Online-File-Storage

This network application creates a peer-to-peer network that facilitates encrypted online file storage.

# Dependencies

- [cryptography.fernet](https://cryptography.io/en/latest/fernet/)

`pip install cryptography`

# Usage

### `class Node`

`Node` contains all the basic functionalities needed to build and navigate the peer-to-peer network i.e. joining the network, connecting/disconnecting to/from specific nodes, handling incoming transmissions, and maintaining a list of peers on the network. This class can easily be extended to create a variety of peer-to-peer applications.

### `class StorageNode`

`StorageNode` is an extension on `Node` that implements file storage functionalities. Nodes may upload data to be stored on the network for future retrieval in a secure and distributed manner. 

The API is very straightforward:
- `StorageNode.uploadFile(filename, encrypt=False)`
- `StorageNode.downloadFile(filename, decrypt=False)`
- `StorageNode.removeFile(filename)`

# Basic Overview

- joining the network

There are no central servers involved. Each `Node` carries a list of connected peers. So to connect, the address of just a single peer is enough. Upon connecting, the new node retrieves the existing node's list of peers and propogates the network with connections.

- uploading data

Files are read in chunks. Each chunk is sent to a set of known peers based on an arbitrary/configured criteria. Additionally, each chunk is hashed and stored in a list. The list is stored in a local dictionary keyed by the filename.

- storing data

Nodes store data received as a single file where the filename is a hash of its contents.

- retrieving data

Files may be requested by their hashes. Nodes may reference their local dictionary to retrieve the list of hashes associated with the file they need. An attempt is then made to find each piece from the list of known peers. Finally, each piece is written in order to recreate the file.

- verification

The encryption functions [handle verification and tamper detection](https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet.decrypt).

- encrypting data

When being uploaded, files are split into chunks. A key is created (custom key option to be added) and used to encrypt each chunk before sending. The same key with a different IV (`os.urandom`) is used for each chunk. Different keys are used for different files, although this may not be necessary.
[`AES128-CBC`](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) [is used](https://cryptography.io/en/latest/fernet/#implementation) for encryption and [`SHA256`](https://en.wikipedia.org/wiki/SHA-2) is used for hashing.

# Additional Features

While this is just an initial implementation with the aforementioned core features, its functionality can be extended easily and significantly. For example:

- `RelayNode`

A node that only maintains and aggressively attempts to update its peer list to facilitate connectivity for new nodes.

- `ReferenceNode`

As mentioned, a local dictionary is kept by nodes which maps your uploaded files to its list of hashes. What if this dictionary is deleted on your device? What if your device is lost? An interesting solution is to upload this local dictionary just as you would any other piece of data. `ReferenceNode`s would be responsible for storing such data and providing users with convenient/alternative authentication methods to retrieve this data.

- Filters

Nodes which receive data currently accept everything. An improvement to this would be to allow for filters which allow nodes to accept data based on a criteria. Filters can also be used when selecting nodes to send data to.

- `BackupNode`

A regular storage node which also sends data it receives to some of its own tracked peers for backup.
