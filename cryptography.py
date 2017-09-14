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


def privkey_to_pubkey(privkey, compressed=True):
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(privkey), curve=ecdsa.SECP256k1)
    pubkey = '04' + sk.get_verifying_key().to_string().hex()
    if compressed:
        return compress_pubkey(pubkey)
    return (pubkey)


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
    if type(data) == str:
        data = bytes.fromhex(data)
    single = hashlib.sha256(data).digest()
    return hashlib.sha256(single).digest()


def pubkey_to_hash160(pubkey):
    pubkey_sha256 = hashlib.sha256(bytes.fromhex(pubkey)).digest()
    return hashlib.new('ripemd160', pubkey_sha256).hexdigest()


def hash160_to_address(r160, p2sh=False):
    pubkey_ver_r160 = '00' + r160 if not p2sh else '05' + r160
    checksum = double_sha256(pubkey_ver_r160).hex()
    address = pubkey_ver_r160 + checksum[:8]
    return base58.b58encode(bytes.fromhex(address))


def pubkey_to_address(pubkey):
    r160 = pubkey_to_hash160(pubkey)
    return hash160_to_address(r160)


def address_to_hash160(address):
    decode = base58.b58decode(address).hex()
    decode, checksum = decode[:-8], decode[-8:]
    digest = double_sha256(decode).hex()
    if checksum != digest[:8]:
        raise ValueError("Invalid checksum")
    return decode[2:]


def redeemScript_to_address(script):
    r160 = pubkey_to_hash160(script)
    return hash160_to_address(r160, p2sh=True)


def generate_signature(pivkey, data):
    _pivkey = bytes.fromhex(pivkey)
    _data = double_sha256(data)
    sk = ecdsa.SigningKey.from_string(_pivkey, curve=ecdsa.SECP256k1)
    return sk.sign_digest(_data, sigencode=ecdsa.util.sigencode_der)


def verify_signature(pubkey, signature, data):
    if pubkey[:2] != '04':
        _pubkey = uncompress_pubkey(pubkey)
    else:
        _pubkey = pubkey
    _pubkey = bytes.fromhex(_pubkey[2:])
    _signature = bytes.fromhex(signature)
    digest = double_sha256(data)
    try:
        vk = ecdsa.VerifyingKey.from_string(_pubkey, curve=ecdsa.SECP256k1)
        vk.verify_digest(_signature, digest, sigdecode=ecdsa.util.sigdecode_der)
        return True
    except:
        return False
    

def main():
    # TESTS
    pubkey = '042e930f39ba62c6534ee98ed20ca98959d34aa9e057cda01cfd422c6bab3667b76426529382c23f42b9b08d7832d4fee1d6b437a8526e59667ce9c4e9dcebcabb'
    pubkey = compress_pubkey(pubkey)
    sig = '30450221009908144ca6539e09512b9295c8a27050d478fbb96f8addbc3d075544dc41328702201aa528be2b907d316d2da068dd9eb1e23243d97e444d59290d2fddf25269ee0e'
    digest = 'c2d48f45d7fbeff644ddb72b0f60df6c275f0943444d7df8cc851b3d55782669'
    data = '01000000018dd4f5fbd5e980fc02f35c6ce145935b11e284605bf599a13c6d41\
            5db55d07a1000000001976a91446af3fb481837fadbb421727f9959c2d32a368\
            2988acffffffff0200719a81860000001976a914df1bd49a6c9e34dfa8631f2c\
            54cf39986027501b88ac009f0a5362000000434104cd5e9726e6afeae357b180\
            6be25a4c3d3811775835d235417ea746b7db9eeab33cf01674b944c64561ce33\
            88fa1abd0fa88b06c44ce81e2234aa70fe578d455dac0000000001000000'
    print (verify_signature(pubkey, sig, data))


if __name__ == "__main__":
    main()