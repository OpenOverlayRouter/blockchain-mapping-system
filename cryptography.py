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

import utils


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
    _privkey = bytes.fromhex(pivkey)
    _data = double_sha256(data)
    sk = ecdsa.SigningKey.from_string(_privkey, curve=ecdsa.SECP256k1)
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


####### Ethereum Like Cryptography #######

def random_privkey():
    key = hex(random.SystemRandom.getrandbits(256))
    key = key[2:-1].zfill(64)
    return bytes.fromhex(key)


def eth_privkey_to_pubkey(privkey):
    sk = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
    pubkey = sk.get_verifying_key().to_string()
    return pubkey


def eth_pubkey_to_address(pubkey):
    return utils.sha3_256(pubkey)[-20:]


def checksum_encode(addr): # Takes a 20-byte binary address as input
    o = ''
    v = utils.big_endian_to_int(utils.sha3(addr))
    for i, c in enumerate(addr.hex()):
        if c in '0123456789':
            o += c
        else:
            o += c.upper() if (v & (2**(255 - 4*i))) else c.lower()
    return '0x'+o


def eth_generate_sign(privkey, data):
    sk = ecdsa.SigningKey.from_string(privkey, curve=ecdsa.SECP256k1)
    return sk.sign_deterministic(bytes.fromhex(data))

def main():
    # TESTS
    '''pubkey = '042e930f39ba62c6534ee98ed20ca98959d34aa9e057cda01cfd422c6bab3667b76426529382c23f42b9b08d7832d4fee1d6b437a8526e59667ce9c4e9dcebcabb'
    pubkey = compress_pubkey(pubkey)
    sig = '30450221009908144ca6539e09512b9295c8a27050d478fbb96f8addbc3d075544dc41328702201aa528be2b907d316d2da068dd9eb1e23243d97e444d59290d2fddf25269ee0e'
    digest = 'c2d48f45d7fbeff644ddb72b0f60df6c275f0943444d7df8cc851b3d55782669'
    data = '01000000018dd4f5fbd5e980fc02f35c6ce145935b11e284605bf599a13c6d41\
            5db55d07a1000000001976a91446af3fb481837fadbb421727f9959c2d32a368\
            2988acffffffff0200719a81860000001976a914df1bd49a6c9e34dfa8631f2c\
            54cf39986027501b88ac009f0a5362000000434104cd5e9726e6afeae357b180\
            6be25a4c3d3811775835d235417ea746b7db9eeab33cf01674b944c64561ce33\
            88fa1abd0fa88b06c44ce81e2234aa70fe578d455dac0000000001000000'
    print (verify_signature(pubkey, sig, data))'''

    k = bytes.fromhex('85e3d0b2bb3011d00a139e5cdc4ae13144962752d6af7916bf2bd271a240094e')
    p = eth_privkey_to_pubkey(k)
    a = eth_pubkey_to_address(p)

    #assert utils.encode_hex(utils.sha3(b'')) == b'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    #print(utils.sha3_256(b'').hex())

    print (a.hex())
    #print (checksum_encode(a))
    print (a)
    print (utils.to_string(a))

    #def test(addrstr):
    #    assert(addrstr == checksum_encode(bytes.fromhex(addrstr[2:])))

    #test('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed')
    #test('0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359')
    #test('0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB')
    #test('0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb')

    v, r, s = eth_generate_sign(k, '1111')
    print(v, r, s)

if __name__ == "__main__":
    main()