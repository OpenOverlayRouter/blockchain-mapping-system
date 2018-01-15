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
    
    
def record_delegation(value, dest, fd):
    fd.write(value + ' ' + dest)

if len(sys.argv) !=5:
    print "Usage: python tx_generator-remotes.py start_prefix node_name node_addresses output_file_name"        
    sys.exit(1)


start = int(sys.argv[1])
node = sys.argv[2]
input_file_name = sys.argv[3]
output_file_name = sys.argv[4]

try:    
    out = open(output_file_name, 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
try:    
    index = open(node+'-delegations.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)    

try:    
    input_addr = open(input_file_name, 'r')
except Exception as e: 
    print e
    sys.exit(1)
origins = []
for line in input_addr:
    origins.append(line)
print "Loaded origins: ", len(origins)
    
try:    
    dests_addr = open('remote-node-addresses.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
dests = []
for line in dests_addr:
    dests.append(line)    
print "Loaded destinations: ", len(dests)
    
    
if node == 'ncalifornia':
    target = 42
elif node == 'nvirginia':
    target = 84
elif node == 'frankfurt':
    target = 126
elif node == 'ireland':
    target = 168
elif node == 'sydney':
    target = 210
elif node == 'tokyo':
    target = 0
else:
    print "Unknown node. Exiting"
    sys.exit(1)
        
count = 0

prefix = '/16'

for i in range(256):
    for j in range(42):
        value = str(start + j) + '.' + str(i) +'.0.0' + prefix
        orig = origins[j]
        des = dests[target % 252]
        write_tx(1, 0, None, des, orig, value, out)
        record_delegation(value, des, index)
        count = count + 1
        target = target + 1        

        
print "Generated", count, "transactions. Exiting"

out.close()
input_addr.close()
dests_addr.close()
index.close()
    

    
    
    
    
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