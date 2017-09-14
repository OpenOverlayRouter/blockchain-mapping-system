import leveldb
from trie import Trie
import random
import string
import utils

N = 50000
print("TEST STARTING")
db = leveldb.LevelDB('./db')
t = Trie(db)
tempDB = {}
print("ADDING SOME NODES...")
for i in range(N):
    value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    key = utils.sha3(value);
    tempDB[key] = value
    t.update(str(key), str(value))
    if(i%10000 == 0):
        print("...")
fail = 0
print("ADDITION FINISHED")
print("CHECKING VALUES...")
cont = 0
for i in tempDB.keys():
    if (t.get(i) != tempDB[i]):
        fail = 1
    cont += 1
    if(cont%10000 == 0):
        print("...")
if fail:
    print ("TEST FAILED")
else:
    print("TEST PASSED")
