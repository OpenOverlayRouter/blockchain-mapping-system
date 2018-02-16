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
    origins4 = open('master-node-addresses-v4.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)

fromv4 = []
for line in origins4:
    fromv4.append(line)
origins4.close()

try:    
    iana6 = open('v6-prefixes-to-delegate', 'r')
except Exception as e: 
    print e
    sys.exit(1)
   

total6 = 41
offset6 = 128
count6 = 0
posv6 = -1
processv6 = True

  
count4 = 0
pos = -1

#v6_subcount = [19, 5, 5, 3, 3, 3, 2, 1]

prefix = '/10'


        
subprefixes = ['0x00', '0x40', '0x80', '0xc0']

for sub in subprefixes:
    for i in range(256):    
        if i % 8 == 0:
            pos = pos + 1
        print pos        

        value = str(i) + '.' + str(int(sub, 0)) + '.0.0' + prefix
        orig = fromv4[i]
        des = node_dest_addr[nodes[i % 8]][pos % 128]
        write_tx(1, 0, None, des, orig, value, out)
        count4 = count4 + 1
        outputs4[nodes[i % 8]].write(value + ' ' + des)
    
        
        
        
        if processv6 and (count6 < total6):
            #Delegate to nodes prefixes specified by input file
            content = iana6.readline()
            if content == '\n':
                processv6 = False
            else:
                if count6 % 8 == 0:
                    posv6 = posv6 + 1
                print "v6pos:", posv6
                content = content.split(' ')            
                value = content[0]
                orig = content[1]
                des = node_dest_addr[nodes[count6 % 8]][posv6 + offset6] 
                write_tx(2, 0, None, des, orig, value, out)
                outputs6[nodes[count6 % 8]].write(value + ' ' + des)
                count6 = count6 + 1
        else:
            if (count4 % 60) == 0:
                processv6 = True

        
print "Generated", count4, "v4 transactions."
print "Generated", count6, "v6 transactions. Exiting"

out.close()
iana6.close()
   


for keys, values in outputs4.iteritems():
    values.close()
for keys, values in outputs6.iteritems():
    values.close()
