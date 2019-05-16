# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:50:44 2019

@author: jordi
"""
#import logger
import logging
import hashlib
import zlib
import ConfigParser
from netaddr import IPAddress


import Consensus.libs.bls_wrapper as bls
import Consensus.dkg as dkg
from shares import Share, Dkg_Share
from own_exceptions import DkgAddContributionSharesError, DkgAddVerificationVectorsError, DkgGenKeysError, DkgGenerateSecretKeyShareError
from own_exceptions import BlsInvalidGroupSignature, BlsSignError, BlsRecoverError



IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
THRESHOLD = config_data.getint('Consensus','dkg_threshold')

#logger.setup_custom_logger('Consensus')
consensusLog = logging.getLogger('Consensus')

#Important: original ids (blockchain addresses expressed in hex) are converted 
#           to integers when used in the DKG
#No problem. Deixo apuntades aquí altres opcions per si es vol seguir investigant:
#- Intentar fer funcionar la funció idVecSerialize de bls.h per un idVec vàlid i analitzar l'output. 
#  Ara que ho penso això potser es pot fer també a partir de la classe Id de C++.
#- Trobar on es definex l'struct "Fr" i mirar com fa la funció serialize/deserialize. 
#  Ens hauria de donar una pista sobre què espera Id per construir-se a partir d'un string.

class Consensus():
    
    def __init__(self, dkg_group, node_ids, randno, group_key, block_no, group_signature):
#TODO: initizlize members correctly                
        self.dkg_group = dkg_group
        self.own_ids = node_ids
        self.current_random_no = randno
        self.secretKeys = {}
        self.group_key = group_key
        self.group_sig =  group_signature
        self.shares = []
        self.shares_ids = []        #These IDs have to be the DKG IDs, not the original blockchain addresses
        self.msg = ''
        self.verified = True
        self.next_signer = None
        self.calculate_next_signer(block_no)
        consensusLog.debug("Next signer: %s", self.next_signer)
        consensusLog.debug("Consensus init, group members: %s", [elem.encode('hex') for elem in self.dkg_group])
        consensusLog.debug("Consensus init, node ids: %s", [elem.encode('hex') for elem in self.own_ids])
        
                
       
    def get_next_signer(self, count):
        return self.next_signer
        
    def get_current_random_no(self):
        return self.current_random_no
        
    def get_current_group_key(self):
        return self.group_key
        
    def get_current_group_sig(self):
        return self.group_sig
    
    def set_current_group_key(self, group_key):
        self.group_key = group_key
        
    def bootstrap_only_set_random_no_manual(self, random_no):
        self.current_random_no = random_no
        
    def bootstrap_only_set_group_sig_manual(self, group_sig):
        self.group_sig = group_sig
        
    #BLS stuff
    def create_shares(self, last_random_no, block_num, count=0):
        self.msg = str(last_random_no) + str(block_num) + str(count)
        digest = hashlib.sha256(self.msg).hexdigest()
        consensusLog.info("Creating new shares with message %s, message hash: %s", self.msg, digest)
        new_shares =  []
        #Create one share for each of the node IDs        
        for oid in self.own_ids:
            sig = bls.sign(digest, self.secretKeys[oid])
            if sig == "":
                raise BlsSignError()
            new_shares.append(Share(oid, sig))
            consensusLog.info("Share content: %s", sig)
        consensusLog.info("Created %s new shares.", len(new_shares))
        #Directly store these shares internally
        for share in new_shares:
            self.store_share(share, self.msg, block_num)
        return new_shares
            
    def store_share(self, share, expected_message, block_no):
        #To obtain the dkg_id we take the first dictionary because the ids are the same for all nodes     
        dkg_id = self.members[self.members.keys()[0]][share.source]['id']
        #Sanity checks: avoid adding already seen shares, do not recompute if enough shares received
        if dkg_id not in self.shares_ids and not self.verified:
            self.shares_ids.append(dkg_id)
            self.shares.append(share.signature)
            consensusLog.info("Stored share from: %s", share.source.encode("hex"))
            if len(self.shares_ids) >= THRESHOLD:
                consensusLog.debug("THRESHOLD shares received. Attempting to verify group signature with message %s", expected_message)
                self.group_sig = bls.recover(self.shares_ids, self.shares)
                if self.group_sig == "":
                    raise BlsRecoverError()
                self.verified = bls.verify(hashlib.sha256(expected_message).hexdigest(), self.group_sig, self.group_key)
                if self.verified:                
                    self.current_random_no = hashlib.sha256(self.group_sig).hexdigest()
                    #TOREMOVE self.next_signer = self.calculate_next_signer(block_no)
                    consensusLog.info("Group signature is: %s", self.group_sig)                    
                    consensusLog.info("Group signature verified correctly. New random number is: %s", self.current_random_no)                    
                    return True
                else:
                    raise BlsInvalidGroupSignature() 
            else:
                return False
        else:
            return False
            
    def verify_group_sig(self, expected_message, block_group_sig):
        return bls.verify(hashlib.sha256(expected_message).hexdigest(), block_group_sig, self.group_key)
        
    def shares_ready(self):
        return self.verified
        
    def reset_bls(self):
        self.shares = []
        self.shares_ids = []
        self.verified = False

        
    #Only when the node DOES NOT PARTICIPATE IN THE DKG-BLS, but wants 
    #to have all the ids available to verify the BLS signatures
    def store_ids(self, new_dkg_group):
        self.dkg_group = new_dkg_group
        self.own_ids = []        
        self.members = {}       
        self.members['no_asociated_dkg'] = {}       
        for oid in new_dkg_group:
            secKey, _ = bls.genKeys(zlib.adler32(oid))
            if secKey == "":
                raise DkgGenKeysError()            
            self.members['no_asociated_dkg'][oid] = {
                "id": secKey,
                "receivedShare": None,
                "vvec": None
            }   
            
    def store_group_key(self, gp_key):
        self.group_key = gp_key
        
        
    #DKG stuff
        
    # Create a new DKG with a new list of members
    #Params: new_dkg_group: list of new blockchain addresses that will participate in this DKG
    #        new_node_ids: id that is calling the function
    #Needs to be called once for each different IDs of the node!!!!
    def new_dkg(self, new_dkg_group, new_node_ids):
        self.members = {}
        self.dkg_group = new_dkg_group
        self.own_ids = new_node_ids
        #Create internal structures
        for node_id in self.own_ids:
            self.members[node_id] = {}
            for oid in new_dkg_group:
                #We have to convert the 160 bit ethereum address to a 32-bit integer because the DKG libarary IDs can 
                #are 32-bit int maximum. However, this is NOT SECURE and a VULNERABILITY. Ideally we should be able 
                # to use the FULL 160 bit address converted to integer as an ID, or its hex string
                secKey, _ = bls.genKeys(zlib.adler32(oid))
                if secKey == "":
                    raise DkgGenKeysError()            
                self.members[node_id][oid] = {
                    "id": secKey,
                    "receivedShare": None,
                    "vvec": None
                }        
        #Generate contributions, for all IDs of this node
        to_send = []
        consensusLog.info("Generating DKG shares for this node. Total number of DKG participants: %s, number of IDs owned by this node: %s.", len(self.dkg_group), len(self.own_ids))
        for node_id, data_node_id in self.members.iteritems():        
        
            vVec, secretContribs = dkg.generateContribution(THRESHOLD, 
                                                   [ member["id"] for _,member in data_node_id.iteritems() ] )
            for contrib in secretContribs:
                if contrib == "":
                    consensusLog.error("Error in generating the secret contributions. Position with error: %s", secretContribs.index(contrib))
                    raise DkgGenerateSecretKeyShareError()
    
            consensusLog.debug("Info from originating node ID: %s", node_id.encode('hex'))            
            consensusLog.debug("vVec lenght: %s", len(vVec))
            consensusLog.debug("secret contribs are: %s", secretContribs)
            
            i = 0
            for oid, member_data in data_node_id.iteritems():
                if oid in self.own_ids:
                    #Store shares for this node_id and the own_ids
                    self.verify_dkg_contribution(Dkg_Share(node_id, oid, secretContribs[i], vVec))
                else:
                    to_send.append(Dkg_Share(node_id, oid, secretContribs[i], vVec))                                        
                    #self.members[oid][node_id]["vvec"] = vVec
                    #self.members[oid][node_id]["receivedShare"] = secretContribs[i]
                i += 1                                               
                                               
        return to_send
        
    def verify_dkg_contribution(self, dkg_contribution):
        oid = dkg_contribution.source
        destination = dkg_contribution.to        #It is one of the node IDs, verified in the upper layer
        contrib = dkg_contribution.secret_share_contrib
        vVec = dkg_contribution.verif_vector
           
        if dkg.verifyContributionShare(self.members[destination][destination]["id"], contrib, vVec):
            self.members[destination][oid]["receivedShare"] = contrib
            self.members[destination][oid]["vvec"] = vVec
            consensusLog.info("Received valid share from member %s" % oid.encode('hex'))
        else:
            consensusLog.warning("Received invalid share from member %s, ignoring..." % oid.encode('hex'))
    
        if self.allSharesReceived(destination):
            #global sk, groupPk
            self.secretKeys[destination] = dkg.addContributionShares( [ member["receivedShare"] for _,member in self.members[destination].iteritems() ])
            if self.secretKeys[destination] == "":
                raise DkgAddContributionSharesError()
            groupsvVec = dkg.addVerificationVectors( [ member["vvec"] for _,member in self.members[destination].iteritems() ])
            #It does not matter if we rewrite it because it is the same for all members in a particular round
            self.group_key = groupsvVec[0]
            if self.group_key == "":
                raise DkgAddVerificationVectorsError()
            consensusLog.info("DKG setup completed for node ID %s", destination.encode('hex'))
            consensusLog.info("Resulting group public key is " + self.group_key + "\n")
            
        
    def allSharesReceived(self, current_id):
        for _,member in self.members[current_id].iteritems():
            if not member["receivedShare"]:
                return False
        return True    
        
    def all_node_dkgs_finished(self):
        for oid in self.own_ids:
            if not self.allSharesReceived(oid):
                return False
        return True
                
    # Returns the IP Address in a readable format
    def formalize_IP(self, IP_bit_list):
        ip = int(IP_bit_list,2)
        return IPAddress(ip)

    # Given a random HASH, returns the selected address in a list
    def consensus_for_IPv6(self, hash):
        ngroup = len(hash)/IPv6_PREFIX_LENGTH
        address = ""
        for i in range (0,len(hash),ngroup):
            ini_xor = int(hash[i],2)
            for j in range (i+1,i+ngroup):
                ini_xor = ini_xor^int(hash[j],2)
            address = address+str(ini_xor)
        return address
    
    # Given a random HASH, returns the selected address in a list
    def consensus_for_IPv4(self, hash):
        ngroup = len(hash)/IPv4_PREFIX_LENGTH
        address = ""
        for i in range (0,len(hash),ngroup):
            ini_xor = int(hash[i],2)
            for j in range (i,i+ngroup):
                ini_xor = ini_xor^int(hash[j],2)
            address = address+str(ini_xor)
        return address

    def calculate_next_signer(self, block_number):
        #Consensus for v4 and v6 operate at bit level, transfrom from hex to bits
        #We assume random number is always encoded in bits (256bits)!!!
        random_no_in_bits = bin(int(self.current_random_no,16))[2:].zfill(256)
        if block_number % 2 != 0: # block_number is the previous one, so if it is even, next should be IPv6
             self.next_signer = self.formalize_IP(self.consensus_for_IPv4(random_no_in_bits))
        else:
             self.next_signer = self.formalize_IP(self.consensus_for_IPv6(random_no_in_bits))
    
    def print_share_array(self, array):
        for share in array:
            print "shares.Share('" + share.source.encode('hex') + "','" + share.signature + "')"
            
    def print_dkg_share_array(self, array):
        for share in array:
            print "shares.Dkg_Share('" + share.source.encode('hex') + "','" + share.to.encode('hex') + "','" + \
                share.secret_share_contrib + "'," + str(share.verif_vector) + ")"

    def bootstrap_master_add_secret_keys_manual(self, manual_keys):
        self.store_ids(self.dkg_group)        
        self.own_ids = self.dkg_group
        self.verified = False
        for oid, key in manual_keys.iteritems():
            self.secretKeys[oid] = key
