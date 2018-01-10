from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from db import _EphemDB
from block import Block, BlockHeader
import time
import transactions
import trie
import rlp
import state
from utils_test import get_rand_tx
from db import LevelDB,_EphemDB
import time
from transactions import Transaction
import copy
from db import _EphemDB
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
from chain_service import ChainService
import sys
import radix

rtree = radix.Radix()

rnode = rtree.add("10.0.0.0/4")
rnode.data["address"] = "1"

rnode = rtree.add("10.0.0.0/26")
rnode.data["address"] = "2"

# Exact search will only return prefixes you have entered
# You can use all of the above ways to specify the address
rnode = rtree.search_best("10.1.0.1")
# Get your data back out
print rnode.data["address"]

# Use the nodes() method to return all RadixNodes created
nodes = rtree.nodes()
for rnode in nodes:
        print rnode.prefix

# The prefixes() method will return all the prefixes (as a
# list of strings) that have been entered
prefixes = rtree.prefixes()

# You can also directly iterate over the tree itself
# this would save some memory if the tree is big
# NB. Don't modify the tree (add or delete nodes) while
# iterating otherwise you will abort the iteration and
# receive a RuntimeWarning. Changing a node's data dict
# is permitted.
for rnode in rtree:
        print rnode.prefix

"""
print "Loading the environment..."
db = LevelDB("./chain")
env = Env(db)

print "Loading chain..."
chain = ChainService(env)
ip6 = IPAddress('45f9:f2c1:7de2:d2f6:4a8d:95ad:98cf:8be0')
for node in chain.chain.patricia.patricia.nodes():
     print node.prefix

print(chain.get_addr_from_ip(str(ip6)).encode("HEX"))
print(chain.get_state().get_balance("be30c5eb90498848da5a5d822b0e1b4939f6fe74").own_ips)
"""

print "empieza test"

arbol = radix.Radix()

for i in range (0, 255):
    nodo = arbol.add("192.168." + str(i) + ".0/24")
    nodo.data["hola"] = str(i)

nodo = arbol.search_exact("192.168.50.0/24")
print nodo.data['hola']

nodo = arbol.search_exact("192.168.40.0/24")
print nodo.data['hola']
