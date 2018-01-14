# -*- coding: utf-8 -*-
import sys


def write_tx(afi, category, metadata, dest, orig, value, fd):
    
    
    fd.write("afi;" + str(afi) + '\n')
    fd.write("category;" + str(category) + '\n')
    fd.write("to;" + dest)
    fd.write("from;" + orig)
    fd.write("value;" + value +'\n')
    
    if metadata is not None:
        fd.write(metadata +'\n')
        
    fd.write("end;\n")


try:    
    out = open('master-transactions.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
    
try:    
    origins = open('master-node-addresses.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
try:    
    dests = open('remote-node-addresses.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
count = 0

prefix = '/8'

for i in range(256):    
    if count < 252:    
        value = str(i) + '.0.0.0' + prefix
        orig = origins.readline()
        des = dests.readline()
        write_tx(1, 0, None, des, orig, value, out)
        count = count + 1
    else:
        print "Finished"
        
print "Generated", count, "transactions. Exiting"

out.close()
origins.close()
dests.close()
    

    
    
    
    
#prefix = '/16'
#for i in range(256):
#    for j in range(256):
#        value = str(i) + '.' + str(j) + '.0.0' + prefix
#        orig = 
#        des = 
#        write_tx(1, 0, None, des, orig, value, out)
#        count++
#
#print "Generated %s transactions. Exiting", count
#print count