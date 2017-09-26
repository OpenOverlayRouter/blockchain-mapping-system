import ipaddress
import rlp
from netaddr import IPNetwork, IPAddress

class Balance(rlp.Serializable):
    fields = [
        ('own_ips', IPNetwork),
        ('delegated_ips', IPNetwork),
        ('recieved_ips', IPNetwork)
    ]

    def __init__(self, own_ips, delegated_ips, recieved_ips):
        self.own_ips = own_ips
        self.delegated_ips = delegated_ips
        self.recieved_ips = recieved_ips
