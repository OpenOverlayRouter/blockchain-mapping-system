#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 16:46:43 2019

@author: jordip
"""

import time
import ConfigParser

config_data = ConfigParser.RawConfigParser()
config_data.read('chain_config.cfg')   
NUM_BLOCKS_CLEAR = config_data.getint('Cache','num_blocks_clear')
BLOCK_TIME = config_data.getint('General','block_time')

class Share_Cache():
    
    def __init__(self):
        self.dkg_share_cache = []
        self.bls_share_cache = []
        self.bls_future_shares = {}
        
        config_data = ConfigParser.RawConfigParser()
        config_data.read('chain_config.cfg')   
        self.last_time_clear = time.time()
        self.clearing_interval = 100000
        #self.clearing_interval = NUM_BLOCKS_CLEAR * BLOCK_TIME
        
    def in_dkg_cache(self, share):
        return share.secret_share_contrib in self.dkg_share_cache
        
    def in_bls_cache(self, share):
        return share.signature in self.bls_share_cache
    
    def store_dkg(self, share):
        if time.time() > (self.last_time_clear + self.clearing_interval):
            self.bls_share_cache = []
            self.dkg_share_cache = []
            self.last_time_clear = time.time()
        self.dkg_share_cache.append(share.secret_share_contrib)
        
    def store_bls(self, share):
        if time.time() > (self.last_time_clear + self.clearing_interval):
            self.bls_share_cache = []
            self.dkg_share_cache = []
            self.last_time_clear = time.time()
        self.bls_share_cache.append(share.signature)
        
    def store_future_bls(self, share):
        try:
            self.bls_future_shares[share.block_number].append(share)
        except KeyError:
            self.bls_future_shares[share.block_number] = []
            self.bls_future_shares[share.block_number].append(share)
            
    def pending_future_bls(self, block_num):
        try:
            if len(self.bls_future_shares[block_num]) > 0:
                return True
            else:
                return False
        except KeyError:
            return False
    
    def get_future_bls(self, block_num):
        return self.bls_future_shares[block_num].pop()