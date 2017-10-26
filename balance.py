import ipaddress
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
import random
import json



class Balance(rlp.Serializable):
    fields = [
        ('own_ips', IPSet),
        ('delegated_ips', {address, IPSet}),
        ('received_ips', {address, IPSet})
    ]

    def __init__(self, own_ips=IPSet(), delegated_ips={}, received_ips={}):
        if(type (own_ips) is not IPSet):
            print ("NOT")
            own_ips = IPSet(own_ips)
        else:
            print ("YES")
        self.own_ips = own_ips
        self.delegated_ips = delegated_ips
        self.received_ips = received_ips
        super(Balance,self).__init__(own_ips,delegated_ips,received_ips)

    def add_own_ips(self, ips):
        len(self.own_ips)
        self.own_ips.add(ips)

    def remove_own_ips(self, ips):
        self.own_ips.remove(ips)

    def add_delegated_ips(self, address, ips):
        n_address = normalize_address(address)
        if n_address in self.delegated_ips.keys():
            self.delegated_ips[n_address].add(ips)
        else:
            self.delegated_ips[n_address] = IPSet(ips)

    def remove_delegated_ips(self, address, ips):
        n_address = normalize_address(address)
        self.delegated_ips[n_address].remove(ips)
        if len(self.delegated_ips[n_address]) == 0:
            self.delegated_ips.pop(n_address)

    def add_received_ips(self, address, ips):
        n_address = normalize_address(address)
        if n_address in self.received_ips.keys():
            self.received_ips[n_address].add(ips)
        else:
            self.received_ips[n_address] = IPSet(ips)

    def remove_received_ips(self, address, ips):
        n_address = normalize_address(address)
        self.received_ips[n_address].remove(ips)
        if len(self.received_ips[n_address]) == 0:
            self.received_ips.pop(n_address)

    def in_own_ips(self,ips):
        print(ips)
        return self.own_ips.__contains__(ips)

    def in_delegated_ips(self,ips):
        for set in self.delegated_ips.itervalues():
            if set.__contains__(ips):
                return True
        return False

    def in_received_ips(self,ips):
        for set in self.received_ips.itervalues():
            if set.__contains__(ips):
                return True
        return False

