# -*- coding: utf-8 -*-
import sys
import netaddr


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
    
    
def generate_v6_prefix(old_pref, new_pref, address, count):
    big_net = netaddr.IPNetwork(address + '/' + old_pref)
    subnets = list(big_net.subnet(int(new_pref)))
    return str(subnets[count-1])
    
 
def v6_left_to_write(pref6):
    for data in pref6:
        if data["num_tx"] != 0:
            return True
    return False

    
if len(sys.argv) !=2:
    print "Usage: python tx_generator_second_level.py node_name"        
    sys.exit(1)


node = sys.argv[1]
nodes = ['ncalifornia', 'canada', 'nvirginia', 'saopaulo', 'ireland', 'frankfurt', 'mumbai', 'singapore', 'sydney', 'tokyo']

if node not in nodes:
    print "Unknwon node!! Exiting"    
    sys.exit(1)

nodes.remove(node)
print "Removed node", node, "from destination list"

#Open output files
try:    
    out = open('intermediate_files/second_level_tx/second_level_tx_' + node + '.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
#It is required to save in different files
outputs4 = {}

for one_node in nodes: 
    try:    
        outputs4[one_node] = open('intermediate_files/second_level_owners/second_level_owners4_' + one_node + '.txt', 'a')
    except Exception as e: 
        print e
        sys.exit(1)  
print "Created output files:"
print outputs4


outputs6 = {}    
for one_node in nodes: 
    try:    
        outputs6[one_node] = open('intermediate_files/second_level_owners/second_level_owners6_' + one_node + '.txt', 'a')
    except Exception as e: 
        print e
        sys.exit(1)
print "Created output files:"
print outputs6


#Load addresses from other nodes to be used as destinations

node_dest_addr = {}
count = 0



for one_node in nodes:    
    print "Loading v4 node destionations dictionaries for", one_node
    node_dest_addr[one_node] = []
    try:    
        node_addr = open('node_addresses/' + one_node + '-addresses.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        node_dest_addr[one_node].append(line)
        count = count + 1
    node_addr.close()
    
print "Total loaded v4 destinantions:", count


dest_addr6 = {}
count = 0
for one_node in nodes:    
    print "Loading v6 node destionations dictionaries for", one_node
    dest_addr6[one_node] = []
    try:    
        node_addr = open('node_addresses/' + one_node + '-addresses6.txt', 'r')
    except Exception as e: 
        print e
        sys.exit(1)
    for line in node_addr:
        dest_addr6[one_node].append(line)
        count = count + 1
    node_addr.close()

print "Total loaded v6 destinantions:", count


#Load current node prefixes and save into memory
try:    
    input4 = open('intermediate_files/first_level_owners/first-level4' + node + '.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)


    
    

#Load allowed expansions for v6
try:    
    allowed6 = open('v6_allowed_intermediate_expansion.csv', 'r')
except Exception as e: 
    print e
    sys.exit(1)
allowed6.readline()
max_exp = {}
for line in allowed6:
    content = line.split(' ')    
#File format    
#content[0] = prefix value
#content[1] = initial prefix
#content[2] = maximum allowed prefix to expand
#content[3] = number of tx to create for this prefix
    max_exp[content[0]] = [content[2], content[3]]
allowed6.close()
print "Number of loaded max. expansions:", len(max_exp)
print max_exp




try:    
    input6 = open('intermediate_files/first_level_owners/first-level6' + node + '.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

#Store in memory v6 prefixes owned by this node
pref6 = []
for line in input6:
    content = line.split(' ')
    data = {}
    addres_only = content[0].split('/')
    data["address"] = addres_only[0]
    data["old_pref"] = addres_only[1]
    data["owner"] = content[1]
    #Add number of tx to create for each prefix
    try:    
        data["num_tx"] = int(max_exp[addres_only[0]][1])
        data["new_pref"] = max_exp[addres_only[0]][0]
        pref6.append(data)
    except KeyError:
        print addres_only[0], "This prefix has not yet been delegated in all v6 files. Skipping"
    
input6.close()

print ("Loaded v6 prefixes: %s",len(pref6))
print pref6

#Total number of nodes   
NUM_NODES = 9
#Number of blockchain addresses of each node
ADDRS_PER_NODE = 250
ADDRS_PER_NODE_V6 = 150

count4 = 0
count6 = 0
global_count = 0
pos = -1


pos6 = -1
pos_des6 = -1


spacings6= {'ncalifornia' : 21, 'canada': 32, 'nvirginia' : 25, 'saopaulo' : 29, 'ireland' : 20, 'frankfurt' : 24, 'mumbai' : 20, 'singapore' : 1000, 'sydney' : 11, 'tokyo' : 25}
V6SPACING = spacings6[node]

#Here we are expanding from /13 to /16, it is 3 bits, we do 8 passes along the input file
expanded = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]
for exp in expanded:
    for line in input4:
        if (count4 % NUM_NODES) == 0:
            pos = pos + 1
                
        content = line.split(' ')
        address = content[0].split('.')
        first_byte = address[0]
        second_byte = address[1]
        owner = content[1]
        
        value = first_byte + '.' + str(int(second_byte) + exp) + '.0.0/16'
        des = node_dest_addr[nodes[count4 % NUM_NODES]][pos % ADDRS_PER_NODE]
        
        
        
        write_tx(1, 0, None, des, owner, value, out)
        record_delegation(value, des, outputs4[nodes[count4 % NUM_NODES]])    
        count4 = count4 + 1
        global_count = global_count + 1
    
        #v6 transactions
        if v6_left_to_write(pref6):
        #Still tx to generate
            if count4 % V6SPACING == 0:
                #We leave some space between v6 tx
                #We have a pointer to the next v6 prefix to use
                pos6 = (pos6 + 1) % len(pref6)           
                data = pref6[pos6] 
                while data["num_tx"] == 0:
                #Jump to next pending tx 
                    pos6 = (pos6 + 1) % len(pref6)
                    data = pref6[pos6]
                #Update destination pointer                
                if count6 % NUM_NODES == 0:
                    pos_des6 = pos_des6 + 1
                   
                value = generate_v6_prefix(data["old_pref"], data["new_pref"], data["address"], data["num_tx"])     
                orig = data["owner"]
                des = dest_addr6[nodes[count6 % NUM_NODES]][(pos_des6 % ADDRS_PER_NODE_V6)]
                
                
                write_tx(2, 0, None, des, orig, value, out)
                record_delegation(value, des, outputs6[nodes[count6 % NUM_NODES]])
                count6 = count6 + 1
                global_count = global_count + 1
                data["num_tx"] = data["num_tx"] - 1
                   
    #Go back to the beginning of the file     
    input4.seek(0)
    
    
for data in pref6:
    if data["num_tx"] != 0:
        print "Prefix", data["address"], "has not delegated all of its addresses!! :(", data["num_tx"], "left to add"
    
         
print "Total tx generated:", global_count
print "Generated", count4, "v4 transactions. Exiting"
print "Generated", count6, "v6 transactions. Exiting"


input4.close()
out.close()

for keys, values in outputs4.iteritems():
    values.close()
for keys, values in outputs6.iteritems():
    values.close()