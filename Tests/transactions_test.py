import utils
from transactions import Transaction
import rlp
from py_ecc.secp256k1 import privtopub
from netaddr import IPNetwork
import cPickle as pickle
import os
from ecdsa import SigningKey, SECP256k1
import random


def mk_random_privkey():
    k = hex(random.getrandbits(256))[2:-1].zfill(64)
    assert len(k) == 64
    return k.decode('hex')

priv = mk_random_privkey()
addr = utils.privtoaddr(priv)
pub = privtopub(priv)
print(priv)
print ("PUB")
print (pub)
print ("ADDR")
print (addr.encode('HEX'))
#self, nonce, to, value, type, data, v=0, r=0, s=0
tx = Transaction(0,"3282791d6fd713f1e94f4bfd565eaa78b3a0599d","192.168.0.2/25",0,b'')
tx.sign(priv)
print(tx.hash.encode('HEX'))
print (tx.ip_network)
print(tx.hash.encode('HEX'))
print(tx.sender.encode('HEX'))