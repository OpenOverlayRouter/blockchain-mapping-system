import rlp #used to encode data
import transaction
import trie
from rlp.sedes import big_endian_int, Binary, binary, CountableList
from utils import hash32, trie_root, address
from Crypto.Hash import keccak
from config import default_config

class BlockHeader:
    fields = [
        ('prevhash', hash32),
        ('timestamp', big_endian_int),
        ('extra_data', binary),
        ('state_root', trie_root),
        ('tx_root', trie_root),
        ('signature'),
        ('signer_addr',address)
    ]

    def __init__(self,
                 prevhash=default_config['GENESIS_PREVHASH'],
                 signer_addr=default_config['GENESIS_COINBASE'],
                 state_root=trie.BLANK_ROOT,
                 tx_root=trie.BLANK_ROOT,
                 timestamp=0,
                 extra_data=''):
        self.prevhash = prevhash
        self.signer_addr = signer_addr
        self.state_root = state_root
        self.tx_root = tx_root
        self.timestamp = timestamp
        self.extra_data = extra_data


class Block:
    fields = [
        ('header', BlockHeader),
        ('transactions', transaction),
        ('uncles', BlockHeader)
    ]

    def __init__(self, header, transactions=None, uncles=None):
        self.header = header
        self.transactions = transactions
        self.uncles = uncles

