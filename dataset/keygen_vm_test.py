# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 13:47:54 2017

@author: jordi
"""

from keystore import Keystore
import sys

node = sys.argv[1]

print ("Generating keys for %s", node)

try:    
    addresses = open('node_addresses/' + node + '-addresses6.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)






#if __name__ == "__main__":




for i in range(150):

    k = Keystore.new('TFG1234', None, 0, None)
#k.path = '/jordi/Desktop/spyder-workspace/blockchaincba/Tests/keystore2/' + k.address.encode("HEX")
    k.save(k)
    addresses.write(k.address.encode("HEX")+'\n')
    print k.address.encode("HEX")

addresses.close()
