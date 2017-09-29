from balance import Balance
from netaddr import IPNetwork, IPAddress
import json
import random


N = 500

balance = Balance()

with open('../genesis.json') as data_file:
    data = json.load(data_file)
def create_rand_net():
    a = random.randint(0,192)
    b = random.randint(0,192)
    c = random.randint(0,192)
    d = random.randint(0,192)
    e = random.randint(24,32)
    return IPNetwork(str(a)+"."+str(b)+"."+str(c)+"."+str(d)+"/"+str(e))
cont = 0
alloc = data['alloc']
addresses = []
for addr, bal in alloc.items():
    addresses.append(addr)

for i in range(N):
    balance.add_own_ips(create_rand_net())
    net = create_rand_net()
    net = create_rand_net()
    addr = addresses[random.randint(0,len(addr))]
    balance.add_delegated_ips(addr,net)
    net = create_rand_net()
    addr = addresses[random.randint(0,len(addr))]
    balance.add_recieved_ips(addr,net)

for i in range(N):
    net = create_rand_net()

    if(balance.in_own_ips(net)):
        balance.remove_own_ips(net)

    net = create_rand_net()
    addr = addresses[random.randint(0,len(addr))]

    net = create_rand_net()
    addr = addresses[random.randint(0,len(addr))]

print(cont)
print(balance.own_ips)
print(balance.delegated_ips)
print(balance.recieved_ips)