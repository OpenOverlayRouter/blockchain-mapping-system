# IPcoins: a blockchain-based mapping system

IPcoins is a blockchain prototype to store IP addresses and prefixes. Similarly to how Bitcoin secures coins, IPcoins allows you to associate IP prefixes to a public key and record your ownership in the blockchain. You can also associate RLOCs and Map Servers to these prefixes to create a secure Mapping System. IPcoins also provides an interface to OOR so it can answer Map Requests. More information in [this IETF draft](https://tools.ietf.org/pdf/draft-paillisse-sidrops-blockchain-01.pdf). 

Please note that this prototype is experimental.

##Creating your keys

In the Python console:
```python
from keystore import Keystore
import sys

k = Keystore.new('<key_password>', None, 0, None)
k.save(k)
#see the key's address
print k.address.encode("HEX")
```

##Running

Before running, make sure:
- The file Tests/transactions.txt exists
- The folder keystore exists

To run:
```bash
python blockchaincba.py
```
## Dependencies

**python:** *2.7.8+*

**py_ecc:** *Elliptic curve crypto* (tested v1.1.3)

**rlp:** *A package for encoding and decoding data in and from Recursive Length Prefix notation* (tested v0.6.0)

**PyCryptodome:** *Cryptographic library* (tested v3.4.7)

**netaddr:** *IP library* (tested v0.7.19)

**ipaddr:** *Google's IP address manipulation library* (tested v2.2.0)

**ipaddress:** *IP library*

**leveldb:** *Database library* (tested v0.194)

**bitcoin:** *Keystore and bitcoin utils* (tested 1.1.42)

**:** *Database library* (tested v0.194)

**twisted** *Event-driven networking engine* (tested 17.9.0)

**pytricia** *Subnet Patricia Trie*

**bitstring** *Socket Messages*

**py-radix** *Alternative Patricia trie*

**ipgetter**

**kademlia** *v0.6

**rpcudp** v2.0

To properly install the last two packages:
```bash
sudo pip install -I kademlia==0.6 rpcudp==2.0
```
To compile the BLS:
sudo apt install libgmp-dev libssl-dev
./Consensus/getDependencies.sh
