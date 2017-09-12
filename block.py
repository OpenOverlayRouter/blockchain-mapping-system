import rlp #used to encode data
import transaction
import trie


class BlockHeader:
    fields = [
        ('prevhash'),
        ('tx_root_trie', trie_root),

    ]


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


