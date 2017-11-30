#from db import LevelDB,_EphemDB
import time
from transactions import Transaction
import copy
#from config import Env
#from chain import Chain
#from genesis_helpers import mk_genesis_data
#from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
#from chain_service import ChainService

print "Loading the environment..."
#db = LevelDB("./chain")
#env = Env(db)


print "Loading keystores"

add1 = "094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2"
add2 = "7719818983cb546d1badee634621dad4214cba25"
add3 = "a3e04410f475b813c01ca77ff12cb277991e62d2"

ks1 = Keystore.load("./keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")
ks2 = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
ks3 = Keystore.load("./keystore/a3e04410f475b813c01ca77ff12cb277991e62d2","TFG1234")

ipNet = IPNetwork('192.0.2.16/12')

print "Starting test"
ip4List = list(IPNetwork('192.0.2.0/15'))
ip6List = list(IPNetwork('2001:db8:0:1:1:1:1:1/111'))
print( len(ip4List),len(ip6List))

i = 0
while i < len(ip4List):

    if((i+1)%2 == 0):
        tx = Transaction(0+i, 0, add2, 1, str(ip4List[i]))
    else:
        tx = Transaction(0+i+1, 0, add2, 2, str(ip6List[i]))
    tx.sign(ks1)
    chain.add_pending_transaction(tx)
    block = chain.create_block(add1)
    block.sign(ks1.privkey)
    chain.add_block(block)

tx1 = Transaction(0, 0, add2, 1, '192.152.0.0/12')
tx1.sign(ks1.privkey)
















