# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 13:34:21 2019

@author: jordi
"""
import sys
import netaddr


def v6_left_to_write(pref6):
    for prefixes, data in pref6.iteritems():
        if data["num_tx"] != 0:
            return True
    return False

def generate_v6_prefix(old_addr_and_pref, new_pref, count):
    big_net = netaddr.IPNetwork(old_addr_and_pref)
    subnets = list(big_net.subnet(int(new_pref)))
    return str(subnets[count-1])
try:    
    output = open('v6-prefixes-to-delegate2.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)


#Load allowed expansions for v6
try:    
    allowed6 = open('v6_master_allowed_expansion.csv', 'r')
except Exception as e: 
    print e
    sys.exit(1)
allowed6.readline()


pref6 = {}
for line in allowed6:
    content = line.split(' ')    
#File format    
#content[0] = prefix value
#content[1] = initial prefix
#content[2] = maximum allowed prefix to expand
#content[3] = number of tx to create for this prefix
#content[4] = blockchain address that owns this prefix
    data = {}    
    data['new_pref'] = content[2]
    data['num_tx'] = int(content[3])
    data['owner'] = content[4].rstrip('\n')
    pref6[content[0]] = data
allowed6.close()
print "Number of loaded prefixes:", len(pref6)


while v6_left_to_write(pref6):
    for prefix, data in pref6.iteritems():
        if data['num_tx'] != 0:
            output.write(generate_v6_prefix(prefix, data["new_pref"], data["num_tx"])   + ' ' + data['owner'] +'\n') 
            data["num_tx"] = data["num_tx"] - 1
    output.write('\n')
    






