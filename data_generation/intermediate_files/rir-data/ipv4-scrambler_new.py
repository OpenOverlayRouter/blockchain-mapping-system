# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 16:55:45 2018

@author: jordi
"""

import sys

#NOTE: can also be used for v6 file!!! Just change the input/output filename :)
#Load prefixes from RIR files
try:    
    in_data = open('all-ipv6-rirs.txt', 'r')
except Exception as e: 
    print e
    sys.exit(1)
    
    
    
#Output file with scrambled data
try:    
    out_data = open('all-ipv6-rirs-scrambled.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)

NUM_BUFFERS = 2000

buffers = []
for i in range(NUM_BUFFERS):
    new_buffer = []    
    buffers.append(new_buffer)


   
pos = 0
for line in in_data:
    buffers[pos % NUM_BUFFERS].append(line)
    pos = pos + 1
    
print "Finished buffer loading"
print "Starting writing"
    
for buf in buffers:
    for line in buf:
        out_data.write(line)
        
in_data.close() 
out_data.close()