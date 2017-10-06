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

env = Env(_EphemDB())
db = env.db
chain = Chain(genesis=mk_genesis_data(env), env=env)
prevhash = chain.head_hash
prevnumber = chain.state.block_number


tx1 = transactions.Transaction(1, '', "192.168.9.1/28", 0, 'data', 1, 1, 1)
tx2 = transactions.Transaction(2, '', "192.170.9.1/28", 0, 'data', 1, 1, 1)
tx3 = transactions.Transaction(3, '', "192.172.9.1/28", 0, 'data', 1, 1, 1)

blocks = []
transact = []
transact.extend([tx1,tx2,tx3])

b1 = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1))

t = trie.Trie(db)
s = state.State(env=env)
for index, tx in enumerate(transact):
    b1.transactions.append(tx)
    t.update(rlp.encode(index), rlp.encode(tx))

b1.header.tx_root = t.root_hash

chain.add_block(b1)
prevhash = b1.hash
++prevnumber
