# -*- coding: utf-8 -*-
import sys
import math
import radix

def write_tx(afi, category, metadata, dest, orig, value, fd):
    
    
    fd.write("afi;" + str(afi) + '\n')
    fd.write("category;" + str(category) + '\n')
    fd.write("to;" + dest)
    fd.write("from;" + orig)
    fd.write("value;" + value +'\n')
    
    if metadata is not None:
        fd.write(metadata +'\n')
        
    fd.write("end;\n")
    
    
#Load prefixes from RIR files
try:    
    rir_data = open('rir-data/all-ipv4-rirs.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

count = 0
prefixes = []
for line in rir_data:    
    content = line.split('|')
    prefix = str (  32 -  int(math.floor(math.log(int(content[4]),2))))
    value = content[3] + '/' + prefix
    prefixes.append(value)
    count = count + 1
print "Loaded ", count, "IPv4 prefixes"
rir_data.close()


#Load all possible destinations
try:    
    dests_addr = open('remote-node-addresses.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
dests = []
for line in dests_addr:
    dests.append(line)    
print "Loaded destinations: ", len(dests)
dests_addr.close()

#load all prefixes from all nodes
nodes = ['ncalifornia', 'nvirginia', 'frankfurt', 'ireland', 'sydney', 'tokyo']
rtree = radix.Radix()
count = 0

for node in nodes:    
    print "Loading delegations from: ", node
    try:    
        delegs = open(node+'-delegations.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in delegs:
        data = line.split(' ')
        rnode = rtree.add(data[0])
        rnode.data['owner'] = data[1]
        rnode.data['node'] = node
        count = count + 1
    delegs.close()

print "Total delegations loaded: ", count

#Open output files
outputs = {}
for node in nodes:
    try:    
        outputs[node] = open(node+'-delegations-rir.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
print "Created output files:"
print outputs
    

#Generate transactions
print "Generating transactions..."
count = 0
missed = 0
for pref in prefixes:
    content = pref.split('/')    
    ip = content[0]
    rnode = rtree.search_best(ip)
    if rnode is not None:
        des = dests[count % 252]
        write_tx(1, 0, None, des, rnode.data['owner'], pref, outputs[rnode.data['node']])
        count = count + 1
    else:
        missed = missed + 1
        
print "Total number of generated transactions:", count, "Exiting"
print "Prefixes not found: ", missed
        


#Close outputs
for node in nodes:
    outputs[node].close()
    
    
