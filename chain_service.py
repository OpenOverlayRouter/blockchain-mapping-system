from block import Block, BlockHeader
from transactions import Transaction
from utils import null_address
import chain
import json
from config import Env
from db import LevelDB
import time
from genesis_helpers import mk_genesis_data
import datetime, threading
from db import _EphemDB
from utils import int_to_big_endian
from apply import validate_transaction
import trie
import state
import rlp
import copy
from apply import apply_transaction

class ChainService():
    """
    Manages the chain and requests to it.
    """

    def __init__(self):
        #self.env = Env(LevelDB("./chain"))
        self.env = Env(_EphemDB())
        self.db = self.env.db
        self.chain = chain.Chain(genesis=mk_genesis_data(self.env), env=self.env)
        self.transactions = []
        self.process_time_queue_periodically()

    def add_transaction(self, tx):
        assert isinstance(tx, Transaction)

        # validate transaction
        try:
            # Transaction validation for broadcasting. Transaction is validated
            # against the current head candidate.
            validate_transaction(self.chain.state, tx)
        except Exception as e:
            print(e)
        self.transactions.append(tx)

    # creates a block with the list of pending transactions, creates its tries and returns it
    def create_block(self):
        self.chain.process_time_queue()
        self.chain.add_block(self.block)
        prevhash = self.chain.head_hash
        prevnumber = self.chain.state.block_number
        self.block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber + 1))
        self.block.transactions = self.transactions
        self.create_tries(self.block)
        self.transactions = []
        return self.block

    # creates the tx_trie and state trie of a block
    def create_tries(self, block):
        t = trie.Trie(self.db)
        s = copy.deepcopy(self.chain.state)
        for index, tx in enumerate(block.transactions):
            t.update(rlp.encode(index), rlp.encode(tx))
            chain.apply_block(s, block, self.db)
            apply_transaction(state, tx)
        block.header.tx_root = t.root_hash
        block.header.state_root = s.trie.root_hash

    # adds the block to the chain
    def add_block(self, block):
        self.chain.add_block(block)
        for tx in block.transactions:
            

    # returns the transaction whose hash is 'tx'
    def get_transaction(self, tx):
        return self.chain.get_transaction(tx)

    # returns the block whose hash is 'block'
    def get_block(self, block):
        return self.chain.get_block(block)

    # returns the block whose number is 'block'
    def get_block_by_number(self, block):
        return self.chain.get_block_by_number(block)

    # returns the list of pending transactions (not yet included in a block)
    def get_pending_transactions(self):
        return self.transactions

    def process_time_queue_periodically(self):
        threading.Timer(120, self.chain.process_time_queue()).start()


