'''
    ecdsa library depencendy
    pip install ecdsa
'''

import ecdsa
import hashlib
import os
import random
import time
import base58


def random_key():
    entropy = str(os.urandom(256//8)) \
        + str(random.randrange(2**256)) \
        + str(int(time.time() * 1000000))
    return hashlib.sha256(entropy.encode('utf-8')).hexdigest()


def privkey_to_pubkey(privkey):
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(privkey), curve=ecdsa.SECP256k1)
    return ('04' + sk.get_verifying_key().to_string().hex())


def compress_pubkey(pubkey):
    point_y = int(pubkey[-64:], 16)
    if point_y & 1:
        return '03' + pubkey[2:66]
    else:
        return '02' + pubkey[2:66]


def uncompress_pubkey(pubkey):
    P = 2**256 - 2**32 - 977
    A = 0
    B = 7
    x_hex = pubkey[2:66].lower()
    x = int(x_hex, 16)
    prefix = pubkey[:2]
    beta = pow(int(x*x*x+A*x+B), int((P+1)//4), int(P))
    y = (P-beta) if ((beta + int(prefix,16)) % 2) else beta
    return '04' + x_hex + '{:064x}'.format(y)


def validate_pubkey(pubkey):
    pass


def double_sha256(data):
    single = hashlib.sha256(bytes.fromhex(data)).digest()
    return hashlib.sha256(single).hexdigest()


def pubkey_to_ripemd160(pubkey):
    pubkey_sha256 = hashlib.sha256(bytes.fromhex(pubkey)).digest()
    return hashlib.new('ripemd160', pubkey_sha256).hexdigest()


def ripemd160_to_address(r160):
    pubkey_ver_r160 = '00' + r160
    checksum = double_sha256(pubkey_ver_r160)
    address = pubkey_ver_r160 + checksum[:8]
    return base58.b58encode(bytes.fromhex(address))


def pubkey_to_address(pubkey):
    r160 = pubkey_to_ripemd160(pubkey)
    return ripemd160_to_address(r160)


def address_to_ripemd160(address):
    return base58.b58decode_check(address).hex()


def verify_sign(pubkey, sign, digest):
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(pubkey[2:]), curve=ecdsa.SECP256k1)
    # Alert, Bitcoin 01 hashtype
    s, junk = ecdsa.der.remove_sequence(bytes.fromhex(sign))
    if junk != '':
        print ('JUNK', junk.hex())
    #assert(junk == '')
    print(s)
    x, s = ecdsa.der.remove_integer(s)
    y, s = ecdsa.der.remove_integer(s)
    s = '{:064x}{:064x}'.format(x,y)
    verify = vk.verify_digest(bytes.fromhex(s), bytes.fromhex(digest), sigdecode=ecdsa.util.sigdecode_der)
    return verify
