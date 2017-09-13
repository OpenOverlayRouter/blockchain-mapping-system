import rlp #used to encode data
import transaction
import trie
from rlp.sedes import big_endian_int, Binary, binary, CountableList
from utils import hash32, trie_root

class BlockHeader:
    fields = [
        ('prevhash', hash32),
        ('tx_root_trie', trie_root),
        ('timestamp', big_endian_int),
        ('extra_data', binary),
        ('signature'),
        ('signer_addr')
    ]

    def __init__(self):
        self.tx_root_trie = trie.BLANK_NODE
        self.timestamp = big_endian_int

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

