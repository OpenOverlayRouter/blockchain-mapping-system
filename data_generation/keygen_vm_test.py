# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 13:47:54 2017

@author: jordi
"""

from keystore import Keystore









#if __name__ == "__main__":
 
for i in range(42):

    k = Keystore.new('TFG1234', None, 0, None)
#k.path = '/jordi/Desktop/spyder-workspace/blockchaincba/Tests/keystore2/' + k.address.encode("HEX")
    k.save(k)
    print k.address.encode("HEX")
