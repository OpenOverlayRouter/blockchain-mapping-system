from rlp.sedes import BigEndianInt, Binary
import rlp
from Crypto.Hash import keccak
import sys
import rlp
from rlp.sedes import big_endian_int, BigEndianInt, Binary
from rlp.utils import decode_hex, encode_hex, ascii_chr, str_to_bytes
from py_ecc.secp256k1 import privtopub, ecdsa_raw_sign, ecdsa_raw_recover

import random

TT256 = 2 ** 256
TT256M1 = 2 ** 256 - 1
TT255 = 2 ** 255
SECP256K1P = 2**256 - 4294968273

if sys.version_info.major == 2:
    def to_string(value):
        return str(value)

    def is_numeric(x):
        return isinstance(x, (int, long))

    def is_string(x):
        return isinstance(x, (str, unicode))

    def encode_int32(v):
        return zpad(int_to_big_endian(v), 32)

else:
    def to_string(value):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return bytes(value, 'utf-8')
        if isinstance(value, int):
            return bytes(str(value), 'utf-8')

    def is_numeric(x): return isinstance(x, int)

    def is_string(x): return isinstance(x, bytes)

    def encode_int32(v):
        return v.to_bytes(32, byteorder='big')

    def encode_int_len(v, length):
        return v.to_bytes(length=length, byteorder='big')

    def bytes_to_int(data):
        return int.from_bytes(data, byteorder='big')

def sha3_256(x):
    return keccak.new(digest_bits=256, data=x).digest()

def sha3(seed):
    return sha3_256(to_string(seed))

def sha3rlp(x):
    return sha3(rlp.encode(x))

def big_endian_to_int(x):
    return big_endian_int.deserialize(str_to_bytes(x).lstrip(b'\x00'))

def int_to_big_endian(x):
    return big_endian_int.serialize(x)

def int_to_bytes(value):
    if isinstance(value, str):
        return value
    return int_to_big_endian(value)

def remove_0x_head(s):
    return s[2:] if s[:2] in (b'0x', '0x') else s

def parse_as_bin(s):
    return decode_hex(s[2:] if s[:2] == '0x' else s)

def parse_as_int(s):
    return s if is_numeric(s) else int('0' + s[2:], 16) if s[:2] == '0x' else int(s)

def int_to_addr(x):
    o = [b''] * 20
    for i in range(20):
        o[19 - i] = ascii_chr(x & 0xff)
        x >>= 8
    return b''.join(o)

def normalize_address(x, allow_blank=False):
    if is_numeric(x):
        return int_to_addr(x)
    if allow_blank and x in {'', b''}:
        return b''
    if len(x) in (42, 50) and x[:2] in {'0x', b'0x'}:
        x = x[2:]
    if len(x) in (40, 48):
        x = decode_hex(x)
    if len(x) == 24:
        assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
        x = x[:20]
    if len(x) != 20:
        raise Exception("Invalid address format: %r" % x)
    return x

def encode_int(v):
    """encodes an integer into serialization"""
    if not is_numeric(v) or v < 0 or v >= TT256:
        raise Exception("Integer invalid or out of range: %r" % v)
    return int_to_big_endian(v)


def zpad(x, l):
    """ Left zero pad value `x` at least to length `l`.
    >>> zpad('', 1)
    '\x00'
    >>> zpad('\xca\xfe', 4)
    '\x00\x00\xca\xfe'
    >>> zpad('\xff', 1)
    '\xff'
    >>> zpad('\xca\xfe', 2)
    '\xca\xfe'
    """
    return b'\x00' * max(0, l - len(x)) + x


def privtoaddr(k):
    k = normalize_key(k)
    x, y = privtopub(k)
    return sha3(encode_int32(x) + encode_int32(y))[12:]

def normalize_key(key):
    if is_numeric(key):
        o = encode_int32(key)
    elif len(key) == 32:
        o = key
    elif len(key) == 64:
        o = decode_hex(key)
    elif len(key) == 66 and key[:2] == '0x':
        o = decode_hex(key[2:])
    else:
        raise Exception("Invalid key format: %r" % key)
    if o == b'\x00' * 32:
        raise Exception("Zero privkey invalid")
    return o

def ecrecover_to_pub(rawhash, v, r, s):
    result = ecdsa_raw_recover(rawhash, (v,r,s))
    if result:
        x, y = result
        pub = encode_int32(x) + encode_int32(y)
    else:
        raise ValueError('Invalid VRS')
    assert len(pub) == 64
    return pub

def ecsign(rawhash, key):
    v, r, s = ecdsa_raw_sign(rawhash, key)
    return v, r, s

def random_privkey():
    key = hex(random.SystemRandom.getrandbits(256))
    key = key[2:-1].zfill(64)
    return bytes.fromhex(key)

def pubkey_to_address(pubkey):
    return sha3_256(pubkey)[-20:]

def ip_to_bytes(addr):
    address, mask = addr.split('/') if '/' in addr else (addr, None)
    b = b''.join([encode_int_len(int(x),1) for x in address.split('.')])
    if mask is not None: b += encode_int_len(int(mask),1)
    return b


def bytes_to_ip(b):
    ip = str(b[0]) + '.' + str(b[1]) + '.' + str(b[2]) + '.' + str(b[3])
    if len(b) == 5: ip += '/' + str(b[4])
    return ip

address = Binary.fixed_length(20, allow_empty=True)
int20 = BigEndianInt(20)
int32 = BigEndianInt(32)
int256 = BigEndianInt(256)
hash32 = Binary.fixed_length(32)
trie_root = Binary.fixed_length(32, allow_empty=True)
null_address = b'\xff' * 20
