import random
from netaddr import IPNetwork
from transactions import Transaction
from utils import sha3



def get_rand_ip():
    a = random.randint(0,192)
    b = random.randint(0,192)
    c = random.randint(0,192)
    d = random.randint(0,192)
    e = random.randint(24,32)
    return str(a)+"."+str(b)+"."+str(c)+"."+str(d)+"/"+str(e)

def get_rand_net():
    IPNetwork(get_rand_ip())

def get_rand_tx():
    to = sha3(random.randint(0,100000))[-20:].encode("HEX")
    return Transaction(random.randint(0,5000), to, get_rand_ip(), 0, 'data')
