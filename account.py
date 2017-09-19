import rlp
from utils import normalize_address, hash32, trie_root, \
    big_endian_int, address, int256, encode_hex, encode_int, \
    big_endian_to_int, int_to_addr, zpad, parse_as_bin, parse_as_int
from rlp.sedes import big_endian_int

import trie
import utils




BLANK_HASH = utils.sha3(b'')
BLANK_ROOT = utils.sha3rlp(b'')

class Account(rlp.Serializable):

    fields = [
        ('nonce', big_endian_int),
        ('balance', big_endian_int)
    ]
