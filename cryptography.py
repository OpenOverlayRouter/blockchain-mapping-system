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


def verify_signature(pubkey, signature, digest):
    _pubkey = bytes.fromhex(pubkey[2:])
    _signature = bytes.fromhex(signature)
    _digest = bytes.fromhex(digest)
    vk = ecdsa.VerifyingKey.from_string(_pubkey, curve=ecdsa.SECP256k1)
    try:
        vk.verify_digest(_signature, _digest, sigdecode=ecdsa.util.sigdecode_der)
        return True
    except:
        return False
    

def main():
    # TESTS
    pubkey = '042e930f39ba62c6534ee98ed20ca98959d34aa9e057cda01cfd422c6bab3667b76426529382c23f42b9b08d7832d4fee1d6b437a8526e59667ce9c4e9dcebcabb'
    sig = '30450221009908144ca6539e09512b9295c8a27050d478fbb96f8addbc3d075544dc41328702201aa528be2b907d316d2da068dd9eb1e23243d97e444d59290d2fddf25269ee0e'
    digest = 'c2d48f45d7fbeff644ddb72b0f60df6c275f0943444d7df8cc851b3d55782669'
    print (verify_signature(pubkey, sig, digest))


if __name__ == "__main__":
    main()