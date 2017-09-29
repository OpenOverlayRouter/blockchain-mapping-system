from balance import Balance
from netaddr import IPNetwork, IPAddress
import json
import random
ip_list = list(IPNetwork('192.0.2.128/28'))
random.shuffle(ip_list)
N = 5000

balance = Balance()

with open('../genesis.json') as data_file:
    data = json.load(data_file)
def create_rand_net():
    a = random.randint(0,192)
    b = random.randint(0,192)
    c = random.randint(0,192)
    d = random.randint(0,192)
    e = random.randint(15,32)
    return IPNetwork(str(a)+"."+str(b)+"."+str(c)+"."+str(d)+"/"+str(e))
cont = 0
alloc = data['alloc']
addresses = []
for addr, bal in alloc.items():
    addresses.append(addr)

for i in range(N):
    balance.add_own_ips(create_rand_net())
    net = create_rand_net()
    if(balance.in_own_ips(net)):
        cont = cont + 1
        balance.remove_own_ips(net)

print(cont)
print(balance.own_ips)
print(balance.recieved_ips)