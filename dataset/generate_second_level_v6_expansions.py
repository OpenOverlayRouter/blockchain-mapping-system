# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 19:10:52 2019

@author: jordi
"""

import sys
import netaddr
import radix

rtree6 = radix.Radix()
count = 0

   
print "Loading v6 delegations from: ", node
try:    
    delegs = open('intermediate_files/second_level_owners/second_level_owners6_' + node + '.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
for line in delegs:
    data = line.split(' ')
    rnode = rtree6.add(data[0])
    rnode.data['owner'] = data[1]
    rnode.data['node'] = node
    count = count + 1
delegs.close()

print "Total v6 delegations loaded: ", count
