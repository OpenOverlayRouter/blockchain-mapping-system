import ipaddress
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress

class Balance(rlp.Serializable):
    fields = [
        ('own_ips', [IPNetwork]),
        ('delegated_ips', [IPNetwork]),
        ('recieved_ips', [IPNetwork])
    ]

    def __init__(self, own_ips=[], delegated_ips=[], recieved_ips=[]):
        self.own_ips = own_ips
        self.delegated_ips = delegated_ips
        self.recieved_ips = recieved_ips

    def add_own_ips(self,ips):
        ip_list = []
        for ip in self.own_ips:
            ip_list.append(ip)
        for ip in ips:
            ip_list.append(ip)
        self.own_ips = netaddr.cidr_merge(ip_list)

    def remove_own_ips(self,ips):
        ip_list = []
        for ip in self.own_ips:
            ip_list.append(ip)
        ip_list.remove(ips)
        self.own_ips = netaddr.cidr_merge(ip_list)


b = Balance([IPNetwork('10.105.205.8/32')])

b.add_own_ips([IPNetwork('10.105.205.8/25')])
print b.own_ips
