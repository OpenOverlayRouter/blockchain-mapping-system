# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:50:44 2019

@author: jordi
"""
import logger
import logging
import hashlib
import zlib
import ConfigParser
import Consensus.libs.bls_wrapper as bls
import Consensus.dkg as dkg
from own_exceptions import InvalidBlsGroupSignature
from netaddr import IPAddress


IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
THRESHOLD = config_data.getint('Consensus','dkg_threshold')

logger.setup_custom_logger('Consensus')
consensusLog = logging.getLogger('Consensus')

#Important: original ids (blockchain addresses expressed in hex) are converted 
#           to integers when used in the DKG
#No problem. Deixo apuntades aquí altres opcions per si es vol seguir investigant:
#- Intentar fer funcionar la funció idVecSerialize de bls.h per un idVec vàlid i analitzar l'output. 
#  Ara que ho penso això potser es pot fer també a partir de la classe Id de C++.
#- Trobar on es definex l'struct "Fr" i mirar com fa la funció serialize/deserialize. 
#  Ens hauria de donar una pista sobre què espera Id per construir-se a partir d'un string.

class Consensus():
    
    def __init__(self, dkg_group, node_ids, randno):
#TODO: initizlize members correctly                
        self.current_ids = dkg_group
        self.own_ids = node_ids
        self.current_random_no = randno
        self.secretKey = None
        self.group_key = None
        self.shares = []
        self.shares_ids = []
        self.msg = ''
        self.verified = False
        self.next_signer = None
        
                
       
    def get_next_signer(self, count):
        return self.next_signer
        
    def get_current_random_no(self):
        return self.current_random_no
        
    def get_current_group_key(self):
        return self.group_key
        
    #BLS stuff
    def create_share(self, prev_rand_no, block_num, my_id, count=0):
        self.msg = str(prev_rand_no) + str(block_num) + str(count)
        digest = hashlib.sha256(self.msg).hexdigest()
        sig = bls.sign(digest, self.secretKey)
        share = {'from': my_id, 'signature': sig}
        return share
            
    def store_share(self, share, expected_message, block_no):
        if share['from'] not in self.shares_ids:
            self.shares_ids.append(share['from'])
            self.shares.append(share['signature'])
            consensusLog.info("Stored share from: %s", share['from'])
            if len(self.shares_ids) >= THRESHOLD:
                consensusLog.debug("THRESHOLD shares received. Attempting to verify group signature with message %.", expected_message)
                self.group_sig = bls.recover(self.shares_ids, self.shares)
                self.verified = bls.verify(hashlib.sha256(expected_message).hexdigest(), self.group_sig, self.group_key)
                if self.verified:                
                    self.current_random_no = hashlib.sha256(self.group_signature).hexdigest()
                    self.calculate_next_signer(block_no)
                    consensusLog.info("Group signature verified correctly. New random number is: %s", self.current_random_no)
                    return True
                else:
                    raise InvalidBlsGroupSignature() 
            else:
                return False
        else:
            return False
            
        
        
        
    def shares_ready(self):
        return self.verified
        
    def reset_bls(self):
        self.shares = []
        self.shares_ids = []
            
        
    #DKG stuff
        
    # Create a new DKG with a new list of members
    #Params: original_ids: list of new blockchain addresses that will participate in this DKG
    #        my_ids: id that is calling the function
    #Needs to be called once for each different IDs of the node!!!!
    def new_dkg(self, original_ids, my_id):
        self.members = {}
        #Create internal structures
        for oid in original_ids:
            #We have to convert the 160 bit ethereum address to a 32-bit integer because the DKG libarary IDs can 
            #are 32-bit int maximum. However, this is NOT SECURE and a VULNERABILITY. Ideally we should be able 
            # to use the FULL 160 bit address converted to integer as an ID, or its hex string
            secKey, _ = bls.genKeys(zlib.adler32(oid))
            self.members[oid] = {
                "id": secKey,
                "receivedShare": None,
                "vvec": None
            }        
        #Generate contributions
        vVec, secretContribs = dkg.generateContribution(THRESHOLD, 
                                               [ member["id"] for _,member in self.members.iteritems() ] )

        consensusLog.debug("vVec lenght: %s", len(vVec))
        consensusLog.debug("secret contribs are: %s", secretContribs)
        to_send = {}                
        i = 0
        for oid, member in self.members.iteritems():
            if oid == my_id:
                self.members[my_id]["vvec"] = vVec
                self.members[my_id]["receivedShare"] = secretContribs[i]
            else:               
                to_send[oid] = {'secret_key_share_contrib': secretContribs[i], 'from': my_id, 'verif_vec': vVec}
            i += 1                                               
                                               
        return to_send
        
    def verify_dkg_contribution(self, dkg_contribution, my_id):
        oid = dkg_contribution['from']
        contrib = dkg_contribution['secret_key_share_contrib']
        vVec = dkg_contribution['verif_vec']

        if dkg.verifyContributionShare(self.members[my_id]["id"], contrib, vVec):
            self.members[oid]["receivedShare"] = contrib
            self.members[oid]["vvec"] = vVec
            consensusLog.info("Received valid share from member %s" % oid)
        else:
            consensusLog.warning("Received invalid share from member %s, ignoring..." % oid)
    
        if self.allSharesReceived():
            #global sk, groupPk
            self.secretKey = dkg.addContributionShares( [ member["receivedShare"] for _,member in self.members.iteritems() ])
            groupsvVec = dkg.addVerificationVectors( [ member["vvec"] for _,member in self.members.iteritems() ])
            self.group_key = groupsvVec[0]
            consensusLog.info("DKG setup completed")
            consensusLog.info("Resulting group public key is " + self.group_key + "\n")
            return True
        else:
            return False
        
    def allSharesReceived(self):
        for _,member in self.members.iteritems():
            if not member["receivedShare"]:
                return False
   
        return True    
                
    # Returns the IP Address in a readable format
    def formalize_IP(IP_bit_list):
        ip = int(IP_bit_list,2)
        return IPAddress(ip)

    # Given a random HASH, returns the selected address in a list
    def consensus_for_IPv6(hash):
        ngroup = len(hash)/IPv6_PREFIX_LENGTH
        address = ""
        for i in range (0,len(hash),ngroup):
            ini_xor = int(hash[i],2)
            for j in range (i+1,i+ngroup):
                ini_xor = ini_xor^int(hash[j],2)
            address = address+str(ini_xor)
        return address
    
    # Given a random HASH, returns the selected address in a list
    def consensus_for_IPv4(hash):
        ngroup = len(hash)/IPv4_PREFIX_LENGTH
        address = ""
        for i in range (0,len(hash),ngroup):
            ini_xor = int(hash[i],2)
            for j in range (i,i+ngroup):
                ini_xor = ini_xor^int(hash[j],2)
            address = address+str(ini_xor)
        return address

    def calculate_next_signer(self, block_number):
        if block_number % 2 != 0: # block_number is the previous one, so if it is even, next should be IPv6
             return self.formalize_IP(self.consensus_for_IPv4(self.current_random_no))
        else:
             return self.formalize_IP(self.consensus_for_IPv6(self.current_random_no))    
        
