# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 12:58:38 2019

@author: jordi
"""
import sys




try:    
    master_addr = open('node_addresses/master-addressesv4.txt', 'r')
except Exception as e: 
        print e
        sys.exit(1) 
        
try:    
    master_addr6 = open('node_addresses/master-addressesv6.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1) 
try:    
    out = open('genesis.json', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
try:    
    v6pref = open('rir-files/ipv6-genesis-prefixes', 'r')
except Exception as e: 
    print e
    sys.exit(1) 


#Write beginning
out.write('{\n')
out.write('  "coinbase": "0x0000000000000000000000000000000000000000",' + '\n')
out.write('  "timestamp": "0x5A4BB9B4",' + '\n')
out.write('  "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",' + '\n')
out.write('  "alloc": [' + '\n')
    
    
#Write ip4
i = 0
j = 0
slash8 = range(256)     
subprefixes = ['0x00', '0x40', '0x80', '0xc0']    
for line in master_addr:
    out.write('  {"' +  line.rstrip('\n') + '":{\n')
    out.write('        "balance":{\n')
    out.write('            "own_ips":["' + str(slash8[i]) + '.' + str(int(subprefixes[j],0)) + '.0.0/10"]\n')
    out.write('        }\n')
    out.write('   }},\n')
    j = j + 1    
    if j==4:
        i = i + 1
        j = 0
    
    
#Write ip6
for line in v6pref:
    out.write('  {"' +  master_addr6.readline().rstrip('\n') + '":{\n')
    out.write('        "balance":{\n')
    out.write('            "own_ips":["' + line.rstrip('\n') + '"]\n')
    out.write('        }\n')
    out.write('   }},\n')    
    
#Write end

#Reomve comma from last line
out.seek(-7, 2)
out.write('   }}\n')
out.write('   ]\n')    
out.write('}')    
    
    
master_addr.close()
master_addr6.close()
out.close()
v6pref.close()