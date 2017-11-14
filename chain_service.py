from block import Block, BlockHeader
from transactions import Transaction
from utils import null_address
import chain
from config import Env
import time
from genesis_helpers import mk_genesis_data
from db import _EphemDB
from apply import validate_transaction
import trie
import state
import rlp
from apply import apply_transaction
from utils import normalize_address
from own_exceptions import UnsignedTransaction


class ChainService():
    """
    Manages the chain and requests to it.
    """

    def __init__(self, env=Env()):
        self.env = env
        self.db = self.env.db
        self.chain = chain.Chain(genesis=mk_genesis_data(self.env), env=self.env)
        self.transactions = []

    def add_pending_transaction(self, tx):
        assert isinstance(tx, Transaction)
        validate_transaction(self.chain.state, tx)
        # validate transaction
        try:
            # Transaction validation for broadcasting. Transaction is validated
            # against the current head candidate.
            if not tx.sender:  # sender is set and validated on Transaction initialization
                raise UnsignedTransaction(tx)
            else:
                if tx.sender == null_address:
                    raise UnsignedTransaction(tx)
        except Exception as e:
            print(e)
        self.transactions.append(tx)

    # creates a block with the list of pending transactions, creates its tries and returns it
    def create_block(self, coinbase):
        self.chain.process_time_queue()
        prevhash = self.chain.head_hash
        prevnumber = self.chain.state.block_number
        coinbase = normalize_address(coinbase)
        block = Block(BlockHeader(timestamp=int(time.time()), prevhash=prevhash, number=prevnumber + 1, coinbase=coinbase))
        snapshot = self.chain.state.to_snapshot()
        s = state.State().from_snapshot(snapshot, Env(_EphemDB()))
        for tx in self.transactions:
            try:
                apply_transaction(s, tx)
                block.transactions.append(tx)
            except Exception as e:
                print (e)
        self._create_tries(block)
        return block

    def validate_transaction(self, tx):
        return self.chain.validate_transaction(tx)

    def validate_block(self):
        self.chain.process_time_queue()
        return self.chain.validate_block()

    def verify_block_signature(self,block,ip):
        return self.chain.verify_block_signature(block,ip)

    # creates the tx_trie and state trie of a block
    def _create_tries(self, block):
        t = trie.Trie(_EphemDB())
        snapshot = self.chain.state.to_snapshot()
        s = state.State().from_snapshot(snapshot, Env(_EphemDB()))
        for index, tx in enumerate(block.transactions):
            t.update(rlp.encode(index), rlp.encode(tx))
            apply_transaction(s, tx)
        block.header.tx_root = t.root_hash
        block.header.state_root = s.trie.root_hash

    # adds the block to the chain and eliminates from the pending transactions those transactions present in the block
    def add_block(self, block):
        assert isinstance(block, Block)
        self.chain.add_block(block)
        for tx in block.transactions:
            if tx in self.transactions:
                self.transactions.remove(tx)
        invalid_tx = []
        for tx in self.transactions:
            try:
                validate_transaction(state,tx)
            except Exception:
                invalid_tx.append(tx)
        if invalid_tx:
            for tx in invalid_tx:
                print "Deleted invalid transaction", tx.hash.encode('HEX')
                self.transactions.remove(tx)


    # returns the transaction whose hash is 'tx'
    def get_transaction(self, tx):
        return self.chain.get_transaction(tx)

    # returns the list of pending transactions (not yet included in a block)
    def get_pending_transactions(self):
        return self.transactions

    def get_head_block(self):
        return self.chain.get_head_block()

    # returns the block whose hash is 'block'
    def get_block(self, block):
        return self.chain.get_block(block)

    # returns the block whose number is 'block'
    def get_block_by_number(self, block):
        return self.chain.get_block_by_number(block)

    # returns the own ips of the address
    def get_own_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).own_ips

    # returns the delegated ips of the address
    def get_delegated_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).delegated_ips

    # returns the received ips of the address
    def get_received_ips(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).received_ips

    # returns the map_server of the address
    def get_map_server(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).map_server

    # returns the locator of the address
    def get_locator(self, address):
        normalize_address(address)
        return self.chain.state.get_balance(address).locator

    # returns the state of the chain
    def get_state(self):
        return self.chain.state

    # creates a transaction with de data in the transaction_data dictionary
    def parse_transaction(self, transaction_data, transaction_num, address):
        return Transaction(self.chain.state.get_nonce(address) + transaction_num + 1, transaction_data["category"],
                           transaction_data["to"], transaction_data["afi"], transaction_data["metadata"])

