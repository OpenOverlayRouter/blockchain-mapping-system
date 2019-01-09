# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:50:44 2019

@author: jordi
"""
import logger
import logging
import hashlib
import ConfigParser
import Consensus.libs.bls_wrapper as bls
import Consensus.dkg as dkg







IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
THRESHOLD = config_data.getint('Consensus','dkg_threshold')

logger.setup_custom_logger('Consensus')
consensusLog = logging.getLogger('Consensus')

#Important: original ids (blockchain addresses expressed in hex) are converted 
#           to integers when used in the DKG

class Consensus():
    
    def __init__(self, dkg_group, node_ids):
        self.current_ids = dkg_group
        self.own_ids = node_ids
#TODO: initizlize members correctly        
        
        #self.secretKey = ''
        #self.group_key = ''
        self.shares = []
        self.shares_ids = []
        self.msg = ''
        #print THRESHOLD
        
       #TODO: adjunst 
    def get_next_signer(self):
        return self.next_signer, self.found_in_chain
        
    #BLS stuff
    def create_share(self, prev_rand_no, block_num, my_id, count=0):
        self.msg = str(prev_rand_no) + str(block_num) + str(count)
        digest = hashlib.sha256(self.msg).hexdigest()
        sig = bls.sign(digest, self.secretKey)
        share = {'from': my_id, 'signature': sig}
        return share
            
    def store_share(self, share):
        if share['from'] not in self.shares_ids:
            self.shares_ids.append(share['from'])
            self.shares.append(share['signature'])
            if len(self.shares_ids) >= THRESHOLD:
                self.group_sig = bls.recover(self.shares_ids, self.shares)
                self.verified = bls.verify(self.msg, self.group_sig, self.groups_key)
                return self.group_sig
            else:
                return None
        else:
            return None
            
        
        
        
        
    #def shares_ready(self):
        
    #DKG stuff
        
    # Create a new DKG with a new list of members
    #Params: original_ids: list of new blockchain addresses that will participate in this DKG
    #        my_ids: id that is calling the function
    #Needs to be called once for each different IDs of the node!!!!
    def new_dkg(self, original_ids, my_id):
        self.members = {}
        #Create internal structures
        for oid in original_ids:
            secKey, _ = bls.genKeys(int(oid,16))
            self.members[oid] = {
                "id": secKey,
                "receivedShare": None,
                "vvec": None
            }        
        #Generate contributions
        vVec, secretContribs = dkg.generateContribution(THRESHOLD, 
                                               [ member["id"] for _,member in self.members.iteritems() ] )

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
        
    def allSharesReceived(self):
        for _,member in self.members.iteritems():
            if not member["receivedShare"]:
                return False
    
        return True    
        