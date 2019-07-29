# IPchain: a blockchain-based mapping system

IPchain is a blockchain prototype to store IP addresses and prefixes. Similarly to how Bitcoin secures coins, IPchain allows you to associate IP prefixes to a public key and record your ownership in the blockchain. You can also associate RLOCs and Map Servers to these prefixes to create a secure Mapping System. IPchain also provides an interface to OOR so it can answer Map Requests. More information in [this IETF draft](https://tools.ietf.org/pdf/draft-paillisse-sidrops-blockchain-01.pdf). 

Please note that this prototype is experimental.

## Creating your keys

In the Python console:
```python
from keystore import Keystore
import sys

k = Keystore.new('<key_password>', None, 0, None)
k.save(k)
#see the key's address
print k.address.encode("HEX")
```

## Installation
First, you need to compile the BLS, then install the python libraries:
```bash
cd blockchain-mapping-system
sudo apt install libgmp-dev libssl-dev
./Consensus/getDependencies.sh
sudo sh install_python_libs.sh
```
## Configuration
The file `chain_config.cfg` allows tuning several parameters of the blockchain, such as the block time or DKG threshold. Before running, make sure:
- `bootstrap_node` points to the IP address of your bootstrap node
- You have specified the amount of participants in the DKG in `dkg_threshold`, and
- The minimum number of participants required to create a random number in `dkg_threshold`


## Running

Before running, make sure:
- The file transactions.txt exists in the main directory
- The folder keystore exists
- The configuration in chain_config.cfg fits your scenario

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

## Utilities
- `install_python_libs.sh` script to install all the requiered packages. Run AFTER compiling the BLS .exe
- `stop.sh`  script to stop the two process of the prototype

## Dataset
The folder `dataset` contains files for an 11-node test, each identified by a city name and master for the bootstrap node. There is a set of keys and transactions for each node. It also conatins some scripts that can help in generating your own dataset.
To replicate the test:
1. Create 11 nodes
2. Install the software
3. Rename the transactions file of each node to transactions.txt, e.g. `mv dataset/transactions/canada-transactions.txt transactions.txt`
4. Move the node keys to the keystore, e.g. `mv dataset/keystores/keystore-canada/* keystore`
5. Create the master private key file, run this script in the master node: `python generate_master_dkg.py` (For 100 DKG participants it takes around 2h)
6. Start all nodes

