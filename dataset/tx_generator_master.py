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

nodes = ['ncalifornia', 'canada', 'nvirginia', 'saopaulo', 'ireland', 'frankfurt', 'mumbai', 'singapore', 'sydney', 'tokyo']

node_dest_addr = {}

count = 0

for node in nodes:    
    print "Loading node address dictionaries ", node
    node_dest_addr[node] = []
    try:    
        node_addr = open('node_addresses/' + node + '-addresses.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        node_dest_addr[node].append(line)
        count = count + 1
    node_addr.close()
    
print "Total loaded v4 addresses:", count

count = 0
node_dest_addr6 = {}
for node in nodes:    
    print "Loading node address dictionaries ", node
    node_dest_addr6[node] = []
    try:    
        node_addr = open('node_addresses/' + node + '-addresses6.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        node_dest_addr6[node].append(line)
        count = count + 1
    node_addr.close()
    
print "Total loaded v6 addresses:", count

#Open output files
outputs4 = {}
for node in nodes:
    try:    
        outputs4[node] = open('intermediate_files/first_level_owners/first-level4' + node+'.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
print "Created output files:"
print outputs4

outputs6 = {}
for node in nodes:
    try:    
        outputs6[node] = open('intermediate_files/first_level_owners/first-level6' + node+'.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
print "Created output files:"
print outputs6




try:    
    out = open('master-transactions.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
   
try:    
    origins4 = open('node_addresses/master-addressesv4.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

fromv4 = []
for line in origins4:
    fromv4.append(line)
origins4.close()

try:    
    iana6 = open('rir-files/v6-prefixes-to-delegate', 'r')
except Exception as e: 
    print e
    sys.exit(1)

#Total number of nodes   
NUM_NODES = 10
#Number of blockchain addresses of each node
ADDRS_PER_NODE = 250
ADDRS_PER_NODE_V6 = 150
total6 = 41
count6 = 0
processv6 = True
global_count = 0
count4 = 0
pos = -1
pos6 = -1


prefix = '/13'


#Expanding /10 to /13
#/10s
subprefixes = [0x00, 0x40, 0x80, 0xc0]
#/13s
sub_subprefixes = [0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38]


for sub_sub in sub_subprefixes:
    for i in range(256*4):
        if count4 % NUM_NODES == 0:
            pos = pos + 1

        
        value = str(i>>2) + '.' + str(subprefixes[i % 4] + sub_sub) + '.0.0' + prefix
        orig = fromv4[i]
        des = node_dest_addr[nodes[count4 % NUM_NODES]][pos % ADDRS_PER_NODE]
        
        write_tx(1, 0, None, des, orig, value, out)
        outputs4[nodes[count4 % NUM_NODES]].write(value + ' ' + des)
        count4 = count4 + 1
        global_count = global_count + 1
        
        if processv6 and (count6 < total6):
            #Delegate to nodes prefixes specified by input file
            content = iana6.readline()
            if content == '\n':
                processv6 = False
            else:
                if count6 % NUM_NODES == 0:
                    pos6 = pos6 + 1
                content = content.split(' ')            
                value = content[0]
                orig = content[1]
                des = node_dest_addr6[nodes[count6 % NUM_NODES]][pos6 % ADDRS_PER_NODE_V6] 
                
                write_tx(2, 0, None, des, orig, value, out)
                outputs6[nodes[count6 % NUM_NODES]].write(value + ' ' + des)
                count6 = count6 + 1
                global_count = global_count + 1
        else:
            if (count4 % 60) == 0:
                processv6 = True

print "Total tx generated:", global_count
print "Generated", count4, "v4 transactions."
print "Generated", count6, "v6 transactions. Exiting"

out.close()
iana6.close()
   


for keys, values in outputs4.iteritems():
    values.close()
for keys, values in outputs6.iteritems():
    values.close()
