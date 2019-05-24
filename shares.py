# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 16:01:43 2018

@author: jordi
"""
import rlp
from rlp.sedes import binary, CountableList, big_endian_int
from utils import address, sha3


class Share(rlp.Serializable):

    fields = [
    ('source', address),        
    ('signature', binary), 
    ('block_number', big_endian_int)

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    

    def __init__ (self, source, signature, block_number):
        
        self.source = source
        self.signature = signature
        self.block_number = block_number

            
    @property
    def hash(self):
        return sha3(rlp.encode(self))

    
class Dkg_Share(rlp.Serializable):
    fields = [
    ('source', address),
    ('to', address),
    ('secret_share_contrib', binary),
    ('verif_vector', CountableList(binary))

#Reserved in case we have to sign the shares
#        ('v', big_endian_int),
#        ('r', big_endian_int),
#        ('s', big_endian_int),
    ]
    
    def __init__ (self, source, to, secret_share_contrib, verif_vector):
        
        self.source = source
        self.to = to
        self.secret_share_contrib = secret_share_contrib
        self.verif_vector = verif_vector
        
    @property
    def hash(self):
        return sha3(rlp.encode(self))
