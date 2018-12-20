# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 16:01:43 2018

@author: jordi
"""
import rlp
from rlp.sedes import text
from utils import address, normalize_address, sha3



class Share(rlp.Serializable):

    fields = [
    ('source', address),        
    ('share', text),

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    

    def __init__ (self, source, share):
        
        src = normalize_address(source, allow_blank=True)

        super(Share, self).__init__(src, share)
            
#The next lines are commentedReserved if we are finally signing the shares
#    def hash_message(self, msg):
#        prefix = b''
#        if self.category == 0:
#            prefix = b'Allocate:\n'
#        elif self.category == 1:
#            prefix = b'Delegate:\n'
#        elif self.category == 2:
#            prefix = b'MapServer:\n'
#        elif self.category == 3:
#            prefix = b'Locator:\n'
#        return sha3(int_to_bytes(len(prefix)) + prefix +
#                    int_to_bytes(len(msg)) + msg)

#    @property
#    def sender(self):
#        if not self._sender:
#            if self.r == 0 and self.s == 0:
#                self._sender = null_address
#            else:
#                if self.v in (27, 28):
#                    vee = self.v
#                    sighash = sha3(rlp.encode(self, UnsignedTransaction))
#                elif self.v >= 37:
#                    vee = self.v - self.network_id * 2 - 8
#                    assert vee in (27, 28)
#                    rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
#                                         :-3] + [self.network_id, '', ''])
#                    sighash = sha3(rlpdata)
#                if self.r >= secpk1n or self.s >= secpk1n or self.r == 0 or self.s == 0:
#                    raise InvalidTransaction("Invalid signature values!")
#
#                pub = ecrecover_to_pub(sighash, self.v, self.r, self.s)
#                if pub == b"\x00"*64:
#                    raise InvalidTransaction(
#                        "Invalid signature (zero privkey cannot sign)")
#                self._sender = sha3(pub)[-20:]
#        return self._sender
#
#    @property
#    def network_id(self):
#        if self.r == 0 and self.s == 0:
#            return self.v
#        elif self.v in (27, 28):
#            return None
#        else:
#            return ((self.v - 1) // 2) - 17

#    def sign (self, key, network_id=None):
#        if network_id is None:
#            rawhash = sha3(rlp.encode(self, UnsignedTransaction))
#        else:
#            assert 1 <= network_id < 2**63 - 18
#            rlpdata = rlp.encode(rlp.infer_sedes(self).serialize(self)[
#                                 :-3] + [network_id, b'', b''])
#            rawhash = sha3(rlpdata)
#
#        key = normalize_key(key)
#        self.v, self.r, self.s = ecsign(rawhash, key)
#        if network_id is not None:
#            self.v += 8 + network_id * 2
#        
#        self._sender = privtoaddr(key)
#        return self

    @property
    def hash(self):
        return sha3(rlp.encode(self))

    
class Dkg_Share(rlp.Serializable):
    fields = [
    ('to', address),
    ('share', text),

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    
    def __init__ (self, to, share):
        
        dest = normalize_address(to, allow_blank=True)

        super(Share, self).__init__(dest, share)    
    
    @property
    def hash(self):
        return sha3(rlp.encode(self))
