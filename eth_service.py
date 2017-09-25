import block
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

    def newBlock(self):
        self.block = block.Block(block.BlockHeader()) #empty header

    def addTransaction(self, transaction):
        self.block.transactions.append(transaction)
        encodedTransaction = utils.sha3rlp(transaction)
        self.block.header.tx_root_trie.update(encodedTransaction, rlp.encode(transaction))

    def getTransactioni(self, transactionIndex):
        return self.block.lock.transactions[transactionIndex]

