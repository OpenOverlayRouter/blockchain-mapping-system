import balance
from netaddr import IPNetwork, IPAddress, IPSet


ip1 = IPNetwork('192.168.0.0/24')
ip2 = IPNetwork('10.1.0.0/24')
ip3 = IPNetwork('143.82.0.0/16')

address1 = '54450450e24286143a35686ad77a7c851ada01a0'
address2 = '00000450e24286143a35686ad77a7c851ada0000'
bal = balance.Balance()

bal.add_delegated_ips(address1, ip1)
bal.add_delegated_ips(address1, ip2)
bal.add_delegated_ips(address2, ip3)

print(bal.delegated_ips)

print "checking address 192.168.0.0/25"
print bal.affected_delegated_ips(IPNetwork('0.0.0.0/0'))

print "checking address 192.168.0.0/24"
print bal.affected_delegated_ips(IPNetwork('192.168.0.0/24'))

print "checking address 192.168.0.0/23"
print bal.affected_delegated_ips(IPNetwork('192.168.0.0/23'))

