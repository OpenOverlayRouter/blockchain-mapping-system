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
    
def extract_v6_prefix(line):
    content = line.split('|')
    return content[3], content[4]
    

#File for v6 prefixes not found
try:    
    v6_not_found = open('v6-not-found-prefixes.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)

#File with v4 skipped prefixes
try:    
    skip4 = open('v4-skipped-prefixes.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)

#Load prefixes from RIR files
try:    
    rir_data = open('intermediate_files/rir-data/all-ipv4-rirs-scrambled.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
count = 0
skipped = 0
prefixes = []
for line in rir_data:    
    content = line.split('|')
    prefix = str (  32 -  int(math.floor(math.log(int(content[4]),2))))
    if (int(prefix) < 16):
        #print "WARNING: found prefix greater than 16. Skipping"
        skip4.write(line)
        skipped = skipped + 1
    else:
        value = content[3] + '/' + prefix
        prefixes.append(value)
        count = count + 1
print "Accepted ", count, "IPv4 prefixes"
print "Skipped", skipped, "IPv4 prefixes with prefix bigger than /16"
rir_data.close()
skip4.close()
total4 = count

#Load prefixes from RIR files v6
try:    
    rir_data6 = open('intermediate_files/rir-data/all-ipv6-rirs-scrambled.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)


nodes = ['ncalifornia', 'nvirginia', 'saopaulo', 'frankfurt', 'ireland', 'mumbai', 'sydney', 'tokyo']

#Load all possible destinations
node_dest_addr = {}
count = 0

for one_node in nodes:    
    print "Loading node destionations dictionaries ", one_node
    node_dest_addr[one_node] = []
    try:    
        node_addr = open('addresses/' + one_node + '-addresses.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        node_dest_addr[one_node].append(line)
        count = count + 1
    node_addr.close()
    
print "Total loaded destinantions:", count

#load all prefixes from all nodes (v4)
rtree = radix.Radix()
count = 0

for node in nodes:    
    print "Loading v4 delegations from: ", node
    try:    
        delegs = open('intermediate_files/second_level_owners/second_level_owners4_' + node + '.txt', 'r')
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

print "Total v4 delegations loaded: ", count

#Load v6 owners
rtree6 = radix.Radix()
count = 0

for node in nodes:    
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


#Open output files
outputs = {}
for node in nodes:
    try:    
        outputs[node] = open('intermediate_files/third_level_tx/third_level_tx_' + node+'.txt', 'w')
    except Exception as e: 
        print e
        sys.exit(1)
print "Created output files:"
print outputs
    

#Generate transactions
print "Generating transactions..."

missed4 = 0
count4 = 0
pos4 = -1

missed6 = 0
count6 = 0
pos6 = -1

offset6 = 128
total6 = 82220



for pref in prefixes:
    content = pref.split('/')    
    ip = content[0]
    rnode = rtree.search_best(ip)
    if rnode is not None:
        if (count4 % 8) == 0:
            pos4 = pos4 + 1
        des = node_dest_addr[nodes[count4 % 8]][pos4 % 128]
        #print 'Prefix',pref, 'found in', rnode
        #print 'Owner', rnode.data['owner'], 'node', rnode.data['node']
        #print "Will be written to", outputs[rnode.data['node']]
        write_tx(1, 0, None, des, rnode.data['owner'], pref, outputs[rnode.data['node']])
        count4 = count4 + 1
    else:
        missed4 = missed4 + 1
        
    #v6 generation
    line = rir_data6.readline()
    if line != '':
        addr, pref = extract_v6_prefix(line)
        rnode = rtree6.search_best(addr)   
        if rnode is not None:
            if count6 % 8 == 0:
                pos6 = pos6 + 1
            des = node_dest_addr[nodes[count6 % 8]][(pos6 % 32) + offset6]
            write_tx(2, 0, None, des, rnode.data['owner'], addr + '/' + pref, outputs[rnode.data['node']])
            count6 = count6 + 1
        else:
            missed6 = missed6 + 1
            v6_not_found.write(line)
        
    if (count4 + count6) % 10000 == 0:
        print "Processed", str(count4+count6), "prefixes, total:",  str(total6 + total4)


        
        
        
        
print "Total number of v4 transactions generated:", count4
print "Total number of v6 transactions generated:", count6
print "v4 prefixes not found: ", missed4
print "v6 prefixes not found: ", missed6
        


#Close outputs
for node in nodes:
    outputs[node].close()
rir_data6.close()
v6_not_found.close()
    
    
    
