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

db = _EphemDB()
env = Env(db)

add1 = "094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2"
add2 = "7719818983cb546d1badee634621dad4214cba25"
add3 = "a3e04410f475b813c01ca77ff12cb277991e62d2"

ks1 = Keystore.load("./keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")
ks2 = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
ks3 = Keystore.load("./keystore/a3e04410f475b813c01ca77ff12cb277991e62d2","TFG1234")

tx1 = Transaction(0, 0, add2, 0, '192.152.0.0/12')
tx1.sign(ks1.privkey)
tx2 = Transaction(0, 0, add3, 0, '192.152.0.0/16')
tx2.sign(ks2.privkey)
tx3 = Transaction(0, 1, add1, 0, '192.152.0.0/24')
tx3.sign(ks3.privkey)
tx4 = Transaction(1, 1, add2, 0, '192.152.0.0/25')
tx4.sign(ks3.privkey)
tx5 = Transaction(2, 0, add1, 0, '192.152.0.0/26')
tx5.sign(ks3.privkey)

chain = ChainService(env)

chain.add_transaction(tx1)
chain.add_transaction(tx2)
chain.add_transaction(tx3)
chain.add_transaction(tx4)

block = chain.create_block()
chain.add_block(block)



