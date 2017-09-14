from rlp.sedes import BigEndianInt, Binary
import rlp
from Crypto.Hash import keccak
import sys
import rlp
from rlp.sedes import big_endian_int, BigEndianInt, Binary
from rlp.utils import decode_hex, encode_hex, ascii_chr, str_to_bytes
import random

# 58 character alphabet used
alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58encode(s):
    n = int(s,16)
    result = ''
    while n > 0:
        result = alphabet[n%58] + result
        n //= 58
    return result


def b58decode(s):
    result = 0
    for i in range(0, len(s)):
        result = result * 58 + alphabet.index(s[i])
    return '{:x}'.format(result).zfill(50)


def to_string(value):
    return str(value)


def sha3(seed):
    return sha3_256(to_string(seed))


def sha3rlp(x):
    return sha3(rlp.encode(x))


def sha3_256(x):
    return keccak.new(digest_bits=256, data=x).digest()


def is_numeric(x):
    return isinstance(x, (int, long))

def is_string(x):
    return isinstance(x, (str, unicode))


def to_string(value):
    return str(value)


def big_endian_to_int(x): return big_endian_int.deserialize(
    str_to_bytes(x).lstrip(b'\x00'))


def int_to_big_endian(x): return big_endian_int.serialize(x)


def int_to_bytes(value):
    if isinstance(value, str):
        return value
    return int_to_big_endian(value)

address = Binary.fixed_length(20, allow_empty=True)
int20 = BigEndianInt(20)
int32 = BigEndianInt(32)
int256 = BigEndianInt(256)
hash32 = Binary.fixed_length(32)
trie_root = Binary.fixed_length(32, allow_empty=True)