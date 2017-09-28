from block import Block, BlockHeader
import transactiondb
import utils
import rlp
import db



class ChainService():

    """
    Manages the chain and requests to it.
    """

    def __init__(self, db):
        self.db = db

    def new_block(self):
        self.block = Block(BlockHeader()) #empty header

    def add_transaction(self, transaction):
        self.block.transactions.append(transaction)
        encodedTransaction = utils.sha3(rlp.encode(transaction))
        self.block.header.tx_root.update(encodedTransaction, rlp.encode(transaction))

    def get_transactioni(self, transactionIndex):
        return self.block.transactions[transactionIndex]


