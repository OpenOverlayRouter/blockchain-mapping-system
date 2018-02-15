import datetime
from db import LevelDB
import time
from config import Env
from keystore import Keystore
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

for i in range(5):
     b = chain.create_block(add1)
     b.sign(ks1.privkey)
     time.now
     chain.add_block(b)
     time.sleep(1)