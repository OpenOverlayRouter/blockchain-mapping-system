import ipaddress
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address


class Balance(rlp.Serializable):
    fields = [
        ('own_ips', IPSet),
        ('delegated_ips', {address, IPSet}),
        ('recieved_ips', {address, IPSet})
    ]

    def __init__(self, own_ips=IPSet(), delegated_ips={}, recieved_ips={}):
        self.own_ips = own_ips
        self.delegated_ips = delegated_ips
        self.recieved_ips = recieved_ips

    def add_own_ips(self, ips):
        self.own_ips.add(ips)

    def remove_own_ips(self, ips):
        self.own_ips.remove(ips)

    def add_delegated_ips(self, address, ips):
        n_address = normalize_address(address)
        if n_address in self.delegated_ips:
            self.delegated_ips[n_address].add(ips)
        else:
            self.delegated_ips[n_address] = IPSet(ips)

    def remove_delegated_ips(self, address, ips):
        n_address = normalize_address(address)
        self.delegated_ips[n_address].remove(ips)
        if len(self.delegated_ips[n_address]) == 0:
            self.delegated_ips.pop(n_address)

    def add_recieved_ips(self, address, ips):
        n_address = normalize_address(address)
        if n_address in self.recieved_ips:
            self.recieved_ips[n_address].add(ips)
        else:
            self.recieved_ips[n_address] = IPSet(ips)

    def remove_recieved_ips(self, address, ips):
        n_address = normalize_address(address)
        self.recieved_ips[n_address].remove(ips)
        if len(self.recieved_ips[n_address]) == 0:
            self.recieved_ips.pop(n_address)

    def in_own_ips(self,ips):
        return self.own_ips.__contains__(ips)

    def in_delegated_ips(self,ips):
        for set in self.delegated_ips.itervalues():
            if set.__contains__(ips):
                return True
        return False

    def in_recieved_ips(self,ips):
        for set in self.recieved_ips.itervalues():
            if set.__contains__(ips):
                return True
        return False


