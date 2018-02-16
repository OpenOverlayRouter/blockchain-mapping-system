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

    
if len(sys.argv) !=2:
    print "Usage: python tx_generator_second_level.py node_name"        
    sys.exit(1)


node = sys.argv[1]
nodes = ['ncalifornia', 'nvirginia', 'saopaulo', 'frankfurt', 'ireland', 'mumbai', 'sydney', 'tokyo']

if node not in nodes:
    print "Unknwon node!! Exiting"    
    sys.exit(1)


#Open output files
try:    
    out = open('intermediate_files/second_level_tx/second_level_tx_' + node + '.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    
try:    
    owners4 = open('intermediate_files/second_level_owners/second_level_owners4_' + node + '.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)    
    
try:    
    owners6 = open('intermediate_files/second_level_owners/second_level_owners6_' + node + '.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)

#Load addresses from other nodes to be used as destinations

node_dest_addr = {}
count = 0

nodes.remove(node)
print ("Removed node %s from destination list", node)

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

#Load current node prefixes and save into memory
try:    
    input4 = open('intermediate_files/first_level_owners/first-level4' + node + '.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

pref4 = []    
for line in input4:
    content = line.split(' ')
    data = {}
    slash8 = content[0].split('.')
    data["prefix"] = slash8[0]
    data["owner"] = content[1]
    pref4.append(data)
    
input4.close()

print ("Loaded v4 prefixes: %s",len(pref4))
print pref4
    
    

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

count4 = 0
count6 = 0
pos = -1
pos6 = -1
offset6 = 128

subprefixes = ['0x00', '0x40', '0x80', '0xc0']

subcount4 = 0

for i in range(64):
    for j in range(4):
        sub = int(subprefixes[j],0)
        for k in range(32):
            if (count4 % 7) == 0:
                pos = pos + 1
            data = pref4[j*32 + k]            
            value = data["prefix"] + '.' + str(sub + i) +'.0.0/16'
            orig = data["owner"]
            des = node_dest_addr[nodes[count4 % 7]][pos % 128]
            write_tx(1, 0, None, des, orig, value, out)
            record_delegation(value, des, owners4)    
            count4 = count4 + 1    
        if (j % 2) == 0:
        #Here, for simplicity, we generate all the v6 tx every 64 v4 tx.
            for data in pref6:
                if data["num_tx"] > 0:
                    if count6 % 7 == 0:
                        pos6 = pos6 + 1
                    #Still tx to generate
                    value = generate_v6_prefix(data["old_pref"], data["new_pref"], data["address"], data["num_tx"])     
                    orig = data["owner"]
                    des = node_dest_addr[nodes[count6 % 7]][(pos6 % 32) + offset6]
                    write_tx(2, 0, None, des, orig, value, out)
                    record_delegation(value, des, owners6)
                    count6 = count6 + 1
                    data["num_tx"] = data["num_tx"] - 1
            

    
for data in pref6:
    if data["num_tx"] != 0:
        print "Prefix", data["address"], "has not delegated all of its addresses!! :(", data["num_tx"], "left to add"
    
         
print "Generated", count4, "v4 transactions. Exiting"
print "Generated", count6, "v6 transactions. Exiting"

out.close()
owners4.close()
owners6.close()
    

    
    
    
    
