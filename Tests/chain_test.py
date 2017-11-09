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
"""
db = LevelDB("./chain")
env = Env(db)
"""
env = Env(_EphemDB())

add1 = "094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2"
add2 = "7719818983cb546d1badee634621dad4214cba25"
add3 = "a3e04410f475b813c01ca77ff12cb277991e62d2"

ks1 = Keystore.load("./keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")
ks2 = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
ks3 = Keystore.load("./keystore/a3e04410f475b813c01ca77ff12cb277991e62d2","TFG1234")

tx1 = Transaction(0, 0, add2, 1, '192.152.0.0/12')
tx1.sign(ks1.privkey)
tx2 = Transaction(0, 0, add3, 1, '192.152.0.0/16')
tx2.sign(ks2.privkey)
tx3 = Transaction(0, 1, add1, 1, '192.152.0.0/24')
tx3.sign(ks3.privkey)
tx4 = Transaction(1, 1, add2, 1, '192.152.0.0/25')
tx4.sign(ks3.privkey)
tx5 = Transaction(2, 0, add1, 1, '192.152.0.0/26')
tx5.sign(ks3.privkey)
tx6 = Transaction(3, 3, add3, 1, '192.152.0.0/16',[2, '2001:cdba:9abc:5678::', 20, 230,1, '5.5.5.5', 45, 50])
tx6.sign(ks3.privkey)
tx7 = Transaction(1, 2, add3, 1, '192.152.0.0/16',[1, '1.1.1.2', '54dbb737eac5007103e729e9ab7ce64a6850a310',
     2, '2001:cdba::3257:9652', '89b44e4d3c81ede05d0f5de8d1a68f754d73d997',
     1, '3.3.3.3', '3a1e02d9ea25349c47fe2e94f4265cd261c5c7ca'])
tx7.sign(ks2.privkey)

chain = ChainService(env)

chain.add_pending_transaction(tx1)

#
#chain.add_pending_transaction(tx3)
#chain.add_pending_transaction(tx4)
#chain.add_pending_transaction(tx5)
#chain.add_pending_transaction(tx6)
#chain.add_pending_transaction(tx7)
block = chain.create_block(add1)
chain.add_block(block)


time.sleep(2)
chain.add_pending_transaction(tx2)
block = chain.create_block(add1)
chain.add_block(block)

time.sleep(2)
chain.add_pending_transaction(tx3)
block = chain.create_block(add1)
chain.add_block(block)


time.sleep(2)
chain.add_pending_transaction(tx4)
block = chain.create_block(add1)
chain.add_block(block)

time.sleep(2)
chain.add_pending_transaction(tx5)
block = chain.create_block(add1)
chain.add_block(block)

time.sleep(2)
chain.add_pending_transaction(tx6)
chain.add_pending_transaction(tx7)
block = chain.create_block(add1)
chain.add_block(block)

print("ADDRESS1")
print(chain.get_own_ips(add1))
print(chain.get_delegated_ips(add1))
print(chain.get_received_ips(add1))
print(chain.get_map_server(add1))
print(chain.get_locator(add1))

print("--------------------------")
print("ADDRESS2")
print(chain.get_own_ips(add2))
print(chain.get_delegated_ips(add2))
print(chain.get_received_ips(add2))
print(chain.get_map_server(add2))
print(chain.get_locator(add2))

print("--------------------------")
print("ADDRESS3")
print(chain.get_own_ips(add3))
print(chain.get_delegated_ips(add3))
print(chain.get_received_ips(add3))
print("map server")
print(chain.get_map_server(add3))
print("locator")
print(chain.get_locator(add3))