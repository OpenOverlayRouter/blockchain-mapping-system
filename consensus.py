# -*- coding: utf-8 -*-
"""
Created on Tue Jan  8 11:50:44 2019

@author: jordi
"""
import logger
import logging
import ConfigParser
import libs.bls_wrapper as bls
import Consensus.dkg as dkg





IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
THRESHOLD = config_data.getint('Consensus','dkg_threshold')

logger.setup_custom_logger('Consensus')
consensusLog = logging.getLogger('Consensus')

class Consensus():
    
    def __init__(self, dkg_group, node_ids):
        self.current_ids = dkg_group
        self.own_ids = node_ids
        self.members = dkg_group
        
        
       #TODO: adjunst 
    def get_next_signer(self):
        return self.next_signer, self.found_in_chain
        
    #BLS stuff
    def create_shares(self, count, block_num, members):
        shares = []
        for member in members:
            shares.append(dkg.generateContribution())
            
            
    def store_share(self, share):
    def shares_ready(self):
        
    #DKG stuff
        
    # Create a new DKG with a new list of members
    #Params: original_ids: list of new blockchain addresses that will participate in this DKG
    #        my_ids: id that is calling the function
    #Needs to be called once for each different IDs of the node!!!!
    def new_dkg(self, original_ids, my_id):
        self.members = {}
        #Create internal structures
        for oid in original_ids:
            secKey, _ = bls.genKeys(oid)
            members[oid] = {
                "id": secKey,
                "receivedShare": None,
                "vvec": None
            }        
        #Generate contributions
        vVec, secretContribs = dkg.generateContribution(THRESHOLD, 
                                               [ member["id"] for _,member in members.iteritems() ] )

        to_send = {}                
        i = 0
        for oid, member in members.iteritems():
            if oid == my_id:
                members[my_id]["vvec"] = vVec
                members[my_id]["receivedShare"] = skContrib[i]
            else:               
                to_send[oid] = {'secret_key_share_contrib': skContrib[i], 'from': my_id}
            i += 1                                               
                                               
        return to_send
        
        
        