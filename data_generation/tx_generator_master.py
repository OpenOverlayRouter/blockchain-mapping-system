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

nodes = ['ncalifornia', 'nvirginia', 'saopaulo', 'frankfurt', 'ireland', 'mumbai', 'sydney', 'tokyo']

node_dest_addr = {}

count = 0

for node in nodes:    
    print "Loading node address dictionaries ", node
    node_dest_addr[node] = []
    try:    
        node_addr = open('addresses/' + node + '-addresses.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        node_dest_addr[node].append(line)
        count = count + 1
    node_addr.close()
    
print "Total loaded addresses:", count






try:    
    out = open('master-transactions.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
try:    
    v4deleg = open('master-v4-deleg.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
try:    
    v6deleg = open('master-v6-deleg.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)    
    
try:    
    origins4 = open('master-node-addresses-v4.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
try:    
    orig6 = open('master-node-addresses-v6.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    




try:    
    iana6 = open('v6-prefixes-to-delegate', 'r')
except Exception as e: 
    print e
    sys.exit(1)

total6 = 38
offset6 = 95

for i in range(6):
    orig6.readline()
    
count4 = 0
count6 = 0
pos = 0

prefix = '/8'

increase =  []


for i in range(256):
    if i % 8  == 0:
        increase.append(i-1)
        
increase.pop(0)
        


for i in range(256):    
    
    value = str(i) + '.0.0.0' + prefix
    orig = origins4.readline()
    des = node_dest_addr[nodes[i % 8]][pos]
    write_tx(1, 0, None, des, orig, value, out)
    count4 = count4 + 1
    v4deleg.write(value + ' ' + des)

    
    
    
    if count6 < total6:        
        orig = orig6.readline()
        value = iana6.readline()
        value = value.rstrip('\n')
        des = node_dest_addr[nodes[i % 8]][pos + offset6] 
        write_tx(2, 0, None, des, orig, value, out)
        count6 = count6 + 1
        v6deleg.write(value + ' ' + des)
    
    print pos        
    
    if i in increase:
        pos = pos + 1


        
print "Generated", count4, "v4 transactions."
print "Generated", count6, "v6 transactions. Exiting"

out.close()
origins4.close()
orig6.close()
iana6.close()
v4deleg.close()
v6deleg.close()    

    
    
    
    
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
