from balance import Balance
from netaddr import IPNetwork, IPAddress
import json
import random
import rlp
import utils
import rlp
from db import OverlayDB, RefcountDB
import rlp
import json
from state import State
from config import Env
from block import BlockHeader
from utils import decode_hex, big_endian_to_int, encode_hex, parse_as_bin, parse_as_int, normalize_address, int_to_big_endian
import utils
import pickle
import json
import random
from db import LevelDB
from utils_test import get_rand_net
#import leveldb
from rlp.utils import decode_hex, ascii_chr, str_to_bytes
def length_prefix(length, offset):
    if length < 56:
        return chr(offset + length)
    else:
        length_string = utils.int_to_big_endian(length)
    return chr(offset + 56 - 1 + len(length_string)) + length_string

def encode_optimized(item):
    if isinstance(item, bytes):
        if len(item) == 1 and ord(item) < 128:
            return item
        prefix = length_prefix(len(item), 128)
    else:
        item = b''.join([encode_optimized(x) for x in item])
        prefix = length_prefix(len(item), 192)
    return prefix + item

N = 500

balance = Balance("0.0.0.0/0")
#balance.add_own_ips(get_rand_net())

"""
with open('../genesis.json') as data_file:
    data = json.load(data_file)
cont = 0
alloc = data['alloc']
addresses = []
for addr, bal in alloc.items():
    addresses.append(addr)

for i in range(N):
    balance.add_own_ips(get_rand_net())
    net = get_rand_net()
    net = get_rand_net()
    addr = addresses[random.randint(0,len(addr))]
    balance.add_delegated_ips(addr,net)
    net = get_rand_net()
    addr = addresses[random.randint(0,len(addr))]
    balance.add_received_ips(addr,net)

for i in range(N):
    net = get_rand_net()

    if(balance.in_own_ips(net)):
        balance.remove_own_ips(net)

    net = get_rand_net()
    addr = addresses[random.randint(0,len(addr))]

    net = get_rand_net()
    addr = addresses[random.randint(0,len(addr))]
from trie import Trie
from Crypto.Hash import keccak
import random
import string
import utils
from db import _EphemDB
DataBase = _EphemDB()

env = Env(LevelDB("./state"))
state = State(env=env)
state.set_balance("17961d633bcf20a7b029a7d94b7df4da2ec5427f", balance)
print(state.get_balance("17961d633bcf20a7b029a7d94b7df4da2ec5427f").own_ips)
print("ASJHDJASH")
"""
b = pickle.dumps(balance)

rlpdata = rlp.encode(b)
print(rlpdata)

b = pickle.loads(rlp.decode(rlpdata))

print(b.own_ips)