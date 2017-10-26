from transactions import Transaction
import copy
from db import _EphemDB
from config import Env
from chain import Chain
from genesis_helpers import mk_genesis_data
from apply import validate_transaction, apply_transaction
from keystore import Keystore
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address


db = _EphemDB()
env = Env(_EphemDB())
chain = Chain(genesis=mk_genesis_data(env), env=env)
state = chain.state
add1 = "094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2"
add2 = "7719818983cb546d1badee634621dad4214cba25"
add3 = "a3e04410f475b813c01ca77ff12cb277991e62d2"

ks1 = Keystore.load("./keystore/094a2c9f5b46416b9b9bd9f1efa1f3a73d46cec2","TFG1234")
ks2 = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
ks3 = Keystore.load("./keystore/a3e04410f475b813c01ca77ff12cb277991e62d2","TFG1234")

tx1 = Transaction(0,0,add2, 0, '192.152.0.0/12')
tx1.sign(ks1.privkey)
tx2 = Transaction(0,0,add3, 0, '192.152.0.0/16')
tx2.sign(ks2.privkey)
tx3 = Transaction(0,1,add1, 0, '192.152.0.0/24')
tx3.sign(ks3.privkey)
tx4 = Transaction(1,1,add2, 0, '192.152.0.0/25')
tx4.sign(ks3.privkey)
tx5 = Transaction(2,0,add1, 0, '192.152.0.0/26')
tx5.sign(ks3.privkey)

apply_transaction(state, tx1)
apply_transaction(state, tx2)
apply_transaction(state, tx3)
apply_transaction(state, tx4)
apply_transaction(state, tx5)

print("ADDRESS1")
print(state.get_balance(add1).own_ips)
print(state.get_balance(add1).delegated_ips)
print(state.get_balance(add1).received_ips)

print("ADDRESS2")
print(state.get_balance(add2).own_ips)
print(state.get_balance(add2).delegated_ips)
print(state.get_balance(add2).received_ips)

print("ADDRESS3")
print(state.get_balance(add3).own_ips)
print(state.get_balance(add3).delegated_ips)
print(state.get_balance(add3).received_ips)

print(state.to_snapshot())