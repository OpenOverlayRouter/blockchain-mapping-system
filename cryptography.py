'''
    ecdsa library depencendy
    pip install ecdsa
'''

import ecdsa
import hashlib
import os
import random
import time
import utils


def random_key():
    entropy = str(os.urandom(256//8)) \
        + str(random.randrange(2**256)) \
        + str(int(time.time() * 1000000))
    return hashlib.sha256(entropy.encode('utf-8')).hexdigest()


def privkey_to_pubkey(privkey):
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(privkey), curve=ecdsa.SECP256k1)
    return ('04' + sk.get_verifying_key().to_string().hex())


def pubkey_to_ripemd160(pubkey):
    pubkey_sha256 = hashlib.sha256(bytes.fromhex(pubkey)).digest()
    return hashlib.new('ripemd160', pubkey_sha256).hexdigest()


def pubkey_to_address(pubkey):
    pubkey_ver_r160 = '00' + pubkey_to_ripemd160(pubkey)
    checksum = hashlib.sha256(hashlib.sha256(\
                    bytes.fromhex(pubkey_ver_r160)).digest()).hexdigest()
    address = pubkey_ver_r160 + checksum[:8]
    return utils.b58encode(address)
