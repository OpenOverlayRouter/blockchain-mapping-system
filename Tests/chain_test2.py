from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from db import _EphemDB
from block import Block, BlockHeader
import time
import transactions
import trie
import rlp
from db import LevelDB, EphemDB
from random import randint

env = Env(LevelDB('./chain'))
chain = Chain(genesis=mk_genesis_data(env), env=env)
prevhash = chain.head_hash
prevnumber = chain.state.block_number

for i in range(0, 20):
    print ("iteration " + str(i))
    block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber + 1))
    t = trie.Trie(EphemDB())
    for j in range (0, 3):
        transaction = transactions.Transaction(i*3 + j, '', "192.172.9.1/28", 0, 'data', 1, 1, 1)
        block.transactions.append(transaction)
        t.update(rlp.encode(j), rlp.encode(transaction))
    block.header.tx_root = t.root_hash
    chain.add_block(block)
    prevhash=block.hash
    prevnumber = prevnumber + 1
    chain.process_time_queue()
    time.sleep(2)  # para que timestamp (padre) != timestamp (hijo)

block = chain.get_block_by_number(2)
print ("nonces for block " + str(2) + ": (" + str(len(block.transactions)) + " transactions in block)")
for tx in block.transactions:
    print(tx.nonce)

rand = randint(0, 20)
block = chain.get_block_by_number(rand)
print ("type of second block: " + str(type(block)))
print ("nonces for block " + str(rand) + ": (" + str(len(block.transactions)) + " transactions in block)")
for tx in block.transactions:
    print(tx.nonce)
