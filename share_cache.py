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
        
        config_data = ConfigParser.RawConfigParser()
        config_data.read('chain_config.cfg')   
        self.last_time_clear = time.time()
        self.clearing_interval = NUM_BLOCKS_CLEAR * BLOCK_TIME
        
    def in_dkg_cache(self, share):
        return share.secret_share_contrib in self.dkg_share_cache
        
    def in_bls_cache(self, share):
        return share.signature in self.bls_share_cache
    
    def store_dkg(self, secret_share_contrib):
        if time.time() > (self.last_time_clear + self.clearing_interval):
            self.bls_share_cache = []
            self.dkg_share_cache = []
            self.last_time_clear = time.time()
        self.dkg_share_cache.append(secret_share_contrib)
        
    def store_bls(self, share):
        if time.time() > (self.last_time_clear + self.clearing_interval):
            self.bls_share_cache = []
            self.dkg_share_cache = []
            self.last_time_clear = time.time()
        self.bls_share_cache.append(share.signature)