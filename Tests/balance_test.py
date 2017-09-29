from balance import Balance
from netaddr import IPNetwork, IPAddress
import json

b = Balance()
b.add_delegated_ips("3282791d6fd713f1e94f4bfd565eaa78b3a0599d", IPNetwork('10.105.205.8/29'))

with open('../genesis.json') as data_file:
    data = json.load(data_file)

alloc = data['alloc']

addresses = []
for addr, balance in alloc.items():
    addresses.append(addr)
print addresses


print b.in_delegated_ips(IPNetwork('10.105.205.8/28'))
