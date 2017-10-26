from keystore import Keystore

ks = Keystore.load("./keystore/7719818983cb546d1badee634621dad4214cba25","TFG1234")
print(ks.privkey.encode("HEX"))
print(ks.pubkey)

ks = Keystore.new("TFG1234")
ks.save(ks)