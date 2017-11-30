from db import LevelDB,_EphemDB
import time
from transactions import Transaction
import copy
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
from chain_service import ChainService

print "Loading the environment..."
db = LevelDB("./chain")
env = Env(db)

print "Loading chain..."
chain = ChainService(env)

print "Loading keystores..."

add1 = "094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2"
add2 = "7719818983cb546d1badee634621dad4214cba25"
add3 = "a3e04410f475b813c01ca77ff12cb277991e62d2"

ks1 = Keystore.load("./keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")
ks2 = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
ks3 = Keystore.load("./keystore/a3e04410f475b813c01ca77ff12cb277991e62d2","TFG1234")

print "Starting test..."

print(chain.get_own_ips(add1))
ip4List = list(IPNetwork('192.0.2.0/28'))
ip6List = list(IPNetwork('2001:db8:0:1:1:1:1:1/124'))


i = 0
nonce = 0
blockNum = 1
"""
print "Adding some Own IP TXs"

while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 0, add2, 1, str(ip4List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 0, add2, 2, str(ip6List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)


ip4List = list(IPNetwork('192.0.2.0/30'))
ip6List = list(IPNetwork('2001:db8:0:1:1:1:1:1/126'))


i = 0
nonce = 0
while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 0, add3, 1, str(ip4List[i]))
        tx.sign(ks2.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 0, add3, 2, str(ip6List[i]))
        tx.sign(ks2.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks2.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)
"""

print "Adding some Delegated IP TXs"

print(chain.get_own_ips(add1))
ip4List = list(IPNetwork('192.168.2.0/28'))
ip6List = list(IPNetwork('2001:db9:0:1:1:1:1:1/124'))

nonce = 0
while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 1, add2, 1, str(ip4List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 1, add2, 2, str(ip6List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)


ip4List = list(IPNetwork('193.168.2.0/28'))
ip6List = list(IPNetwork('2002:db9:0:1:1:1:1:1/124'))


i = 0
while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 1, add3, 1, str(ip4List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 1, add3, 2, str(ip6List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)

print "Overlaping som IPs"

print(chain.get_own_ips(add1))
ip4List = list(IPNetwork('192.168.2.0/28'))
ip6List = list(IPNetwork('2001:db9:0:1:1:1:1:1/124'))

nonce = 64
while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 0, add3, 1, str(ip4List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 0, add3, 2, str(ip6List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)


ip4List = list(IPNetwork('193.168.2.0/28'))
ip6List = list(IPNetwork('2002:db9:0:1:1:1:1:1/124'))


i = 0
while i < len(ip4List):
    if(blockNum%2 == 0):
        tx = Transaction(nonce, 0, add2, 1, str(ip4List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
        i += 1
    else:
        tx = Transaction(nonce, 0, add2, 2, str(ip6List[i]))
        tx.sign(ks1.privkey)
        chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)
    nonce += 1
    blockNum += 1
    time.sleep(1)

chain.query_eid("193.168.2.0",0)

print("ADDRESS1")
print "Own IPS"
print(chain.get_own_ips(add1))
print "Delegated IPS"
print(chain.get_delegated_ips(add1))
print "Received IPS"
print(chain.get_received_ips(add1))
print "Map Server"
print(chain.get_map_server(add1))
print "Locator"
print(chain.get_locator(add1))

print("--------------------------")
print("ADDRESS2")
print "Own IPS"
print(chain.get_own_ips(add2))
print "Delegated IPS"
print(chain.get_delegated_ips(add2))
print "Received IPS"
print(chain.get_received_ips(add2))
print "Map Server"
print(chain.get_map_server(add2))
print "Locator"
print(chain.get_locator(add2))

print("--------------------------")
print("ADDRESS3")
print "Own IPS"
print(chain.get_own_ips(add3))
print "Delegated IPS"
print(chain.get_delegated_ips(add3))
print "Received IPS"
print(chain.get_received_ips(add3))
print "Map Server"
print(chain.get_map_server(add3))
print "Locator"
print(chain.get_locator(add3))

















