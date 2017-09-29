from block import Block, BlockHeader
from transactiondb import Transaction
from utils import null_address
import rlp
import db
import chain


def validate_transaction(state, tx):

    # (1) The transaction signature is valid;
    if not tx.sender:  # sender is set and validated on Transaction initialization
        raise Exception('unsigned transaction')

    #assert check_signature(state.config, state.block_number, tx) #TODO: hacer funcion check_signature

    # (2) the transaction nonce is valid (equivalent to the
    #     sender account's current nonce);
    req_nonce = 0 if tx.sender == null_address else state.get_nonce(tx.sender)
    if req_nonce != tx.nonce:
        raise Exception('invalid nonce')

    # (3) check that the address sending an IP address has it

    #check_ip_address(tx.ffrom) #TODO: hacer funcion check_ip_address

    return True


class ChainService():
    """
    Manages the chain and requests to it.
    """

    def __init__(self, db):
        self.db = db
        self.chain = chain.Chain()
        self.block = Block(BlockHeader())

    def add_transaction(self, tx):
        assert isinstance(tx, Transaction)

        # validate transaction
        try:
            # Transaction validation for broadcasting. Transaction is validated
            # against the current head candidate.
            validate_transaction(self.chain.state, tx)
        except Exception as e:
            print(e)

    # adds a transaction to the block
    def _add_transaction_to_block(self, tx):
        self.block.transactions.append(tx)

    # adds a block to the chain
    def add_block(self, block):
        self.chain.add_block(block)

    def get_transaction_i(self, transactionIndex):
        return self.block.transactions[transactionIndex]

