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


def validate_transaction(state, tx):
    unsigned = False
    # (1) The transaction signature is valid;
    if tx.v is None or tx.s is None or tx.r is None:  # sender is set and validated on Transaction initialization
        unsigned = True
        raise Exception('unsigned transaction')

    #assert check_signature(state.config, state.block_number, tx) #TODO: hacer funcion check_signature

    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);
    req_nonce = 0 if unsigned is True else state.get_nonce(tx.sender) #TODO: cambiar tx.sender por funcion para
    if req_nonce != tx.nonce:                                         #TODO: obtenerlo a partir de v, r, s
        raise Exception('invalid nonce')

    # (3) check that the address sending an IP address has it

    #check_ip_address(tx.ffrom) #TODO: hacer funcion check_ip_address

    return True


class ChainService():
    """
    Manages the chain and requests to it.
    """

    def __init__(self):
        #self.env = Env(LevelDB("./chain"))
        self.env = Env(_EphemDB())
        self.db = self.env.db
        self.chain = chain.Chain(genesis=mk_genesis_data(self.env), env=self.env)
        prevhash = self.chain.head_hash
        prevnumber = self.chain.state.block_number
        self.block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1))
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
        self.block.transactions.append(tx)

    # adds the current block to the chain and generates a new one
    def add_block(self):
        self.chain.process_time_queue()
        self.chain.add_block(self.block)
        prevhash = self.block.header.hash
        prevnumber = self.block.header.number
        self.block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber+1))

    # gets the transaction in index i of the current block
    def get_transaction_i(self, transactionIndex):
        return self.block.transactions[transactionIndex]


    def get_block_in_position_i(self, position):
        return self.chain.get_block_by_number(position)

    def process_time_queue_periodically(self):
        threading.Timer(120, self.chain.process_time_queue()).start()


