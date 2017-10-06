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

env = Env(LevelDB('./chain'))
db = _EphemDB()
chain = Chain(genesis=mk_genesis_data(env), env=env)
prevhash = chain.head_hash
prevnumber = chain.state.block_number

N = 5

for iter in range(0,N):
    prevnumber += 1
    transact = []
    for i in range(0,150):
        transact.append(get_rand_tx())

    b = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber))
    time.sleep(1)

    t = trie.Trie(db)
    s = state.State(env=env)
    for index, tx in enumerate(transact):
        b.transactions.append(tx)
        t.update(rlp.encode(index), rlp.encode(tx))

    b.header.tx_root = t.root_hash

    chain.add_block(b)
    prevhash = b.hash
    chain.process_time_queue()
    print(b.number)

print(b)
print(chain.get_block_by_number(50))
