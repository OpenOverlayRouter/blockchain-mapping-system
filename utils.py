from rlp.sedes import BigEndianInt, Binary
import rlp
from Crypto.Hash import keccak

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

address = Binary.fixed_length(20, allow_empty=True)
int20 = BigEndianInt(20)
int32 = BigEndianInt(32)
int256 = BigEndianInt(256)
hash32 = Binary.fixed_length(32)
trie_root = Binary.fixed_length(32, allow_empty=True)