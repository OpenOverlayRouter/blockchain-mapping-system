import rlp
from utils import normalize_address, hash32, trie_root, \
    big_endian_int, address, int256, encode_int, \
    big_endian_to_int, int_to_addr, zpad, parse_as_bin, parse_as_int
from rlp.sedes import big_endian_int, binary
from securetrie import SecureTrie
from trie import Trie
from db import RefcountDB, BaseDB
from balance import Balance
import ipaddress

import trie
import utils




BLANK_HASH = utils.sha3(b'')
BLANK_ROOT = utils.sha3rlp(b'')

class Account(rlp.Serializable):
    fields = [
        ('nonce', big_endian_int),
        ('balance', binary)
    ]

    def __init__(self, nonce, balance, env, address):
        assert isinstance(env.db, BaseDB)
        self.env = env
        self.address = address
        super(Account, self).__init__(nonce, balance)
        self.storage_cache = {}
        self.storage_trie = SecureTrie(Trie(RefcountDB(self.env.db)))
        self.touched = False
        self.existent_at_start = True
        self._mutable = True
        self.deleted = False


    def commit(self):
        for k, v in self.storage_cache.items():
            if v:
                self.storage_trie.update(utils.encode_int32(k), rlp.encode(v))
            else:
                self.storage_trie.delete(utils.encode_int32(k))
        self.storage_cache = {}
        self.storage = self.storage_trie.root_hash

    @property
    def code(self):
        return self.env.db.get(self.code_hash)

    @classmethod
    def blank_account(cls, env, address, initial_nonce=0):
        env.db.put(BLANK_HASH, b'')
        o = cls(initial_nonce, 0, env, address)
        o.existent_at_start = False
        return o

    def is_blank(self):
        return self.nonce == 0 and self.balance == 0 and self.code_hash == BLANK_HASH

    @property
    def exists(self):
        if self.is_blank():
            return self.touched or (
                self.existent_at_start and not self.deleted)
        return True

    def to_dict(self):
        odict = self.storage_trie.to_dict()
        for k, v in self.storage_cache.items():
            odict[utils.encode_int(k)] = rlp.encode(utils.encode_int(v))
        return {'balance': str(self.balance), 'nonce': str(self.nonce)}