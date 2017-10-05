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

blocks = []
transact = []
transact.append(transactions.Transaction(1, '', "192.168.9.1/28", 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transact.append(transactions.Transaction(2, '', "192.170.9.1/28", 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transact.append(transactions.Transaction(3, '', "192.172.9.1/28", 0, 'data', 1, 1, 1))

blocks.append(Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1)))

t = trie.Trie(db)
s = state.State(env=env)

for tx in transact:
    blocks[0].transactions.append(tx)
    t.update(str(tx.hash), str(rlp.encode(tx)))

blocks[0].header.tx_root = t

chain.add_block(blocks[0])
prevhash = blocks[0].hash
++prevnumber
# FIRST BLOCK CREATED

t2 = trie.Trie(db)

blocks.append(Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1)))

transact.append(transactions.Transaction(4, '', "192.168.0.1/24", 0, 'data', 1, 1, 1))
blocks[1].transactions.append(transact[3])
t2.update(str(transact[3].hash), str(rlp.encode(transact[3])))
blocks[1].header.tx_root = t2

chain.add_block(blocks[1])
prevhash = blocks[1].hash
++prevnumber

# SECOND BLOCK CREATED

t3 = trie.Trie(db)

blocks.append(Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1)))

transact.append(transactions.Transaction(4, '', "192.168.0.2/24", 0, 'data', 1, 1, 1))
blocks[2].transactions.append(transact[4])
t2.update(str(transact[4].hash), str(rlp.encode(transact[4])))
blocks[2].header.tx_root = t3

chain.add_block(blocks[2])

# THIRD BLOCK CREATED