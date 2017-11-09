import ipaddress
import rlp
import netaddr
from netaddr import IPNetwork, IPAddress, IPSet
from utils import address, normalize_address
import random
import json
from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address, Bytes
from utils import bytes_to_int, ipaddr_to_netaddr



class Balance(rlp.Serializable):
    fields = [
        ('own_ips', IPSet),
        ('delegated_ips', {address, IPSet}),
        ('received_ips', {address, IPSet}),
        ('map_server', {IPSet, address}),
        ('locator', {address, list})
    ]

    def __init__(self, own_ips=IPSet(), delegated_ips={}, received_ips={}, map_server={}, locator={}):
        if(type (own_ips) is not IPSet):
            own_ips = IPSet(own_ips)
        self.own_ips = own_ips
        self.delegated_ips = delegated_ips
        self.received_ips = received_ips
        self.map_server = map_server
        self.locator = locator
        super(Balance,self).__init__(own_ips,delegated_ips,received_ips,map_server,locator)

    def add_own_ips(self, ips):
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
        self.delegated_ips[n_address] = self.delegated_ips[n_address] - ips
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
        self.received_ips[n_address] = self.received_ips[n_address] - ips
        if len(self.received_ips[n_address]) == 0:
            self.received_ips.pop(n_address)

    def in_own_ips(self,ips):
        return self.own_ips.__contains__(ips)

    def affected_delegated_ips(self, ips):
        ips = IPSet(ips)
        addresses = {}
        for addr, set in self.delegated_ips.iteritems():
            joint = ips&set
            if len(joint) > 0:
                addresses[addr.encode('HEX')] = joint
        return addresses

    def in_received_ips(self,ips):
        for set in self.received_ips.itervalues():
            if set.__contains__(ips):
                return True
        return False

    def set_map_server(self, map_server):
        self.map_server = {}
        for i in range (0, len(map_server), 3):
            afi = bytes_to_int(map_server[i])
            ip = ipaddr_to_netaddr(afi,map_server[i+1])
            address = map_server[i+2]
            self.map_server[ip] = address

    def get_map_server(self):
        return self.map_server

    def set_locator(self, locator):
        self.locator = {}
        l = [None] * 2
        for i in range (0, len(locator), 4):
            afi = bytes_to_int(locator[i])
            ip = ipaddr_to_netaddr(afi,locator[i+1])
            priority = bytes_to_int(locator[i+2])
            weight = bytes_to_int(locator[i+3])
            l[0] = priority
            l[1] = weight
            self.locator[ip] = l

    def get_locator(self):
        return self.locator