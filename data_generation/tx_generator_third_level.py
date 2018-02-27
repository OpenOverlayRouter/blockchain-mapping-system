# -*- coding: utf-8 -*-
import sys
import math
import radix
import netaddr

TX_DIST = 60

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
    
def tx_left_in_buffer(pending_buf):
    node_list = []
    for node, array in pending_buf.iteritems():
        if len(array) != 0:
            node_list.append(node)
    return node_list
        
        

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
    
#Create temporary tx buffer to avoid 'from' repetition
from_buffer = {}
for node in nodes:
    from_buffer[node] = []

#stores 
pending4_tx = {}
for node in nodes:
    pending4_tx[node] = []
pending6_tx = {}
for node in nodes:
    pending6_tx[node] = []
    
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
        if rnode.data['owner'] in from_buffer[rnode.data['node']]:
            #TX from already used in some of the last 60 tx. Wait before writing
            pending4_tx[rnode.data['node']].append(rnode)
        else:
            #TX_DIST is respected. OK to write this tx
            if len(from_buffer[rnode.data['node']]) < TX_DIST:
                 from_buffer[rnode.data['node']].append(rnode.data['owner'])
            else:
                from_buffer[rnode.data['node']].pop(0)
                from_buffer[rnode.data['node']].append(rnode.data['owner'])
            #Normal operation    
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
    #try to write pending v4 tx
    node_list = tx_left_in_buffer(pending4_tx)
    for node in node_list:
        to_remove = []
        for rnode in pending4_tx[node]:
            if rnode.data['owner'] not in from_buffer[node]:
                #we can write this TX
                from_buffer[rnode.data['node']].pop(0)
                from_buffer[rnode.data['node']].append(rnode.data['owner'])
                to_remove.append(rnode)
                #Normal operation                    
                if (count4 % 8) == 0:
                    pos4 = pos4 + 1
                des = node_dest_addr[nodes[count4 % 8]][pos4 % 128]
                write_tx(1, 0, None, des, rnode.data['owner'], rnode.prefix, outputs[rnode.data['node']])
                count4 = count4 + 1
         #Remove tx from the v6 queue                
        for rnode in to_remove:
            pending4_tx[node].remove(rnode)                                
    
    #v6 generation
        
    line = rir_data6.readline()
    if line != '':
        addr, pref = extract_v6_prefix(line)
        rnode = rtree6.search_best(addr)          
        if rnode is not None:
            if rnode.data['owner'] in from_buffer[rnode.data['node']]:
                #TX from already used in some of the last 60 tx. Wait before writing
                pending6_tx[rnode.data['node']].append(rnode)
            else:
                #TX_DIST is respected. OK to write this tx
                if len(from_buffer[rnode.data['node']]) < TX_DIST:
                    from_buffer[rnode.data['node']].append(rnode.data['owner'])
                else:
                    from_buffer[rnode.data['node']].pop(0)
                    from_buffer[rnode.data['node']].append(rnode.data['owner'])
                
                #Normal operation
                if count6 % 8 == 0:
                    pos6 = pos6 + 1
                des = node_dest_addr[nodes[count6 % 8]][(pos6 % 32) + offset6]
                write_tx(2, 0, None, des, rnode.data['owner'], addr + '/' + pref, outputs[rnode.data['node']])
                count6 = count6 + 1
                #check if we can remove some tx from the queue of this node in particular
                to_remove = []
                for rnode in pending6_tx[rnode.data['node']]:
                    if rnode.data['owner'] not in from_buffer[rnode.data['node']]:
                        #we can write this TX
                        from_buffer[rnode.data['node']].pop(0)
                        from_buffer[rnode.data['node']].append(rnode.data['owner'])
                        to_remove.append(rnode)
                        #Normal operation                    
                        if count6 % 8 == 0:
                            pos6 = pos6 + 1
                        des = node_dest_addr[nodes[count6 % 8]][(pos6 % 32) + offset6]
                        write_tx(2, 0, None, des, rnode.data['owner'], rnode.prefix, outputs[rnode.data['node']])
                        count6 = count6 + 1
                 #Remove tx from the v6 queue                
                for rnode in to_remove:
                    pending6_tx[rnode.data['node']].remove(rnode)                    
        else:
            missed6 = missed6 + 1
            v6_not_found.write(line)
    else:
        #write pending tx after all v6 prefixes have been read, for all nodes
        node_list = tx_left_in_buffer(pending6_tx)
        for node in node_list:
            to_remove = []
            for rnode in pending6_tx[node]:
                if rnode.data['owner'] not in from_buffer[node]:
                    #we can write this TX
                    from_buffer[rnode.data['node']].pop(0)
                    from_buffer[rnode.data['node']].append(rnode.data['owner'])
                    to_remove.append(rnode)
                    #Normal operation                    
                    if count6 % 8 == 0:
                        pos6 = pos6 + 1
                    des = node_dest_addr[nodes[count6 % 8]][(pos6 % 32) + offset6]
                    write_tx(2, 0, None, des, rnode.data['owner'], rnode.prefix, outputs[rnode.data['node']])
                    count6 = count6 + 1
             #Remove tx from the v6 queue                
            for rnode in to_remove:
                pending6_tx[node].remove(rnode)                                
            
    if (count4 + count6) % 10000 == 0:
        print "Processed", str(count4+count6), "prefixes, total:",  str(total6 + total4)

for node in nodes:
    if len(pending4_tx[node]) != 0:
        print len(pending4_tx[node]), "pending tx for v4 in node", node
    if len(pending6_tx[node]) != 0:
        print len(pending6_tx[node]), "pending tx for v6 in node", node
        
print "Attempting buffer purge"        
for node in nodes:
    to_remove = []
    for rnode in pending4_tx[node]:
        if rnode.data['owner'] not in from_buffer[node]:
            #we can write this TX
            from_buffer[rnode.data['node']].pop(0)
            from_buffer[rnode.data['node']].append(rnode.data['owner'])
            to_remove.append(rnode)
            #Normal operation                    
            if (count4 % 8) == 0:
                pos4 = pos4 + 1
            des = node_dest_addr[nodes[count4 % 8]][pos4 % 128]
            write_tx(1, 0, None, des, rnode.data['owner'], rnode.prefix, outputs[rnode.data['node']])
            count4 = count4 + 1
     #Remove tx from the v4 queue                
    for rnode in to_remove:
        pending4_tx[node].remove(rnode)  
    to_remove = []
    for rnode in pending6_tx[node]:
        if rnode.data['owner'] not in from_buffer[node]:
            #we can write this TX
            from_buffer[rnode.data['node']].pop(0)
            from_buffer[rnode.data['node']].append(rnode.data['owner'])
            to_remove.append(rnode)
            #Normal operation                    
            if count6 % 8 == 0:
                pos6 = pos6 + 1
            des = node_dest_addr[nodes[count6 % 8]][(pos6 % 32) + offset6]
            write_tx(2, 0, None, des, rnode.data['owner'], rnode.prefix, outputs[rnode.data['node']])
            count6 = count6 + 1
     #Remove tx from the v6 queue                
    for rnode in to_remove:
        pending6_tx[node].remove(rnode)                                
        
        

        

for node in nodes:
    if len(pending4_tx[node]) != 0:
        print len(pending4_tx[node]), "pending tx for v4 in node", node
    if len(pending6_tx[node]) != 0:
        print len(pending6_tx[node]), "pending tx for v6 in node", node

print "Total number of v4 transactions generated:", count4
print "Total number of v6 transactions generated:", count6
print "v4 prefixes not found: ", missed4
print "v6 prefixes not found: ", missed6


print "Dumping pending prefixes to files"

try:    
    notused4 = open('intermediate_files/third_level_debug_files/v4notused.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
try:    
    notused6 = open('intermediate_files/third_level_debug_files/v6notused.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)

for node in nodes:
    for rnode in pending4_tx[node]:
        notused4.write(rnode.data['node']+ ' ' + rnode.data['owner'] + ' ' + rnode.prefix)
    for rnode in pending6_tx[node]:
        notused6.write(rnode.data['node']+ ' ' + rnode.data['owner'] + ' ' + rnode.prefix)

notused4.close()
notused6.close()
#Close outputs
for node in nodes:
    outputs[node].close()
rir_data6.close()
v6_not_found.close()
    
print "Done"    
    
