import sys


try:    
    notused4 = open('intermediate_files/third_level_debug_files/v4notused.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
    
    
try:    
    notused6 = open('intermediate_files/third_level_debug_files/v6notused.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
nodes = ['ncalifornia', 'nvirginia', 'saopaulo', 'frankfurt', 'ireland', 'mumbai', 'sydney', 'tokyo']



nodes_data4 = {}
for node in nodes:
    nodes_data4[node] = {}
    nodes_data4[node]['owners'] = []
    nodes_data4[node]['count'] = []
    
print "Processing v4"

for line in notused4:
    data = line.split(' ')
    node = data[0]    
    owner = data[1]
    if owner not in nodes_data4[node]['owners']:
        nodes_data4[node]['owners'].append(owner)
        nodes_data4[node]['count'].append(1)
    else:
        pos = nodes_data4[node]['owners'].index(owner)
        nodes_data4[node]['count'][pos] = nodes_data4[node]['count'][pos] + 1
        
    
    

print "Finished"
print "Processing v6"

nodes_data6 = {}
for node in nodes:
    nodes_data6[node] = {}
    nodes_data6[node]['owners'] = []
    nodes_data6[node]['count'] = []
    
for line in notused6:
    data = line.split(' ')
    node = data[0]    
    owner = data[1]
    if owner not in nodes_data6[node]['owners']:
        nodes_data6[node]['owners'].append(owner)
        nodes_data6[node]['count'].append(1)
    else:
        pos = nodes_data6[node]['owners'].index(owner)
        nodes_data6[node]['count'][pos] = nodes_data6[node]['count'][pos] + 1    
    
print "Finished"    
print "Results v4"    

for node, data in nodes_data4.iteritems():
    if len(data['owners']) == len(data['count']):
        print node + 'number of repeated addresses:' + str(len(data['owners']))
        print "Address                              Times repeated"
        for addr, count in zip(data['owners'], data['count']):
            print addr + ' ' + str(count)
    else:
        print "FATAL ERROR: count and owner lenght mismatch"


print "Results v6"    
for node, data in nodes_data6.iteritems():
    if len(data['owners']) == len(data['count']):
        print node + 'number of repeated addresses:' + str(len(data['owners']))
        print "Address                              Times repeated"
        for addr, count in zip(data['owners'], data['count']):
            print addr + ' ' + str(count)
    else:
        print "FATAL ERROR: count and owner lenght mismatch"
    
    
    
    
    
    
    
notused4.close()
notused6.close()