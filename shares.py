# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 16:01:43 2018

@author: jordi
"""
import rlp
from rlp.sedes import Binary
from utils import address, normalize_address, sha3



class Share(rlp.Serializable):

    fields = [
    ('source', address),        
    ('signature', Binary)

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    

    def __init__ (self, source, share):
        
        src = normalize_address(source, allow_blank=False)

        super(Share, self).__init__(src, share)
            
    @property
    def hash(self):
        return sha3(rlp.encode(self))

    
class Dkg_Share(rlp.Serializable):
    fields = [
    ('source', address),
    ('to', address),
    ('secret_share_contrib', Binary),
    ('vVec', Binary)

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    
    def __init__ (self, source, to, share, verif_vector):
        
        origin = normalize_address(source, allow_blank=False)
        dest = normalize_address(to, allow_blank=False)

        super(Dkg_Share, self).__init__(origin, dest, share, verif_vector)    
    
    @property
    def hash(self):
        return sha3(rlp.encode(self))