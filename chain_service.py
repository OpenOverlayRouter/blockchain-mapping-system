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

    # creates a block with the list of pending transactions, signs it and adds it to the chain
    def create_block(self):
        self.chain.process_time_queue()
        self.chain.add_block(self.block)
        prevhash = self.chain.head_hash
        prevnumber = self.chain.state.block_number
        self.block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber + 1))
        self.block.transactions = self.transactions
        self.create_tries(self.block)


    # creates the tx_trie and state trie of a block
    def create_tries(self, block):
        t = trie.Trie(self.db)
        s = self.chain.state
        for index, tx in enumerate(block.transactions):
            t.update(rlp.encode(index), rlp.encode(tx))
            s.increment_nonce(tx.sender)
            
        block.header.tx_root = t.root_hash


    # gets the transaction in index i of the current block
    def get_transaction_i(self, transactionIndex):
        return self.block.transactions[transactionIndex]


    def get_block_in_position_i(self, position):
        return self.chain.get_block_by_number(position)

    def process_time_queue_periodically(self):
        threading.Timer(120, self.chain.process_time_queue()).start()


