import rlp #used to encode data
import transactions
import trie
from rlp.sedes import big_endian_int, Binary, binary, CountableList
from utils import hash32, trie_root, address, encode_hex
import utils
from Crypto.Hash import keccak
from config import default_config
from transactions import Transaction

class BlockHeader(rlp.Serializable):
    fields = [
        ('prevhash', hash32),
        ('timestamp', big_endian_int),
        ('extra_data', binary),
        ('state_root', trie_root),
        ('tx_root', trie_root),
        ('number', big_endian_int),
        ('coinbase',address)
    ]

    def __init__(self,
                 prevhash=default_config['GENESIS_PREVHASH'],
                 state_root=trie.BLANK_ROOT,
                 tx_root=trie.BLANK_ROOT,
                 number=0,
                 timestamp=0,
                 coinbase=default_config['GENESIS_COINBASE'],
                 extra_data=''):
        self.prevhash = prevhash
        self.coinbase = coinbase
        self.state_root = state_root
        self.tx_root = tx_root
        self.number = number
        self.timestamp = timestamp
        self.extra_data = extra_data

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self))

    @property
    def hex_hash(self):
        return encode_hex(self.hash)

class FakeHeader():

    def __init__(self, hash='\x00' * 32, number=0, timestamp=0):
        self.hash = hash
        self.number = number
        self.timestamp = timestamp

    def to_block_header(self):
        return BlockHeader(
            number=self.number,
            timestamp=self.timestamp
        )

class Block(rlp.Serializable):
    fields = [
        ('header', BlockHeader),
        ('transactions', CountableList(Transaction))
    ]

    def __init__(self, header, transactions=None):
        self.header = header
        self.transactions = transactions or []

    def __getattribute__(self, name):
        try:
            return rlp.Serializable.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.header, name)

    @property
    def transaction_count(self):
        return len(self.transactions)