# -*- coding: utf-8 -*-
import sys

try:    
    out = open('transactions-master.txt', 'w')
except Exception as e: 
    print e
    sys.exit(1)
    

    
def write_tx(afi, category, metadata=None, dest, orig, value, fd):
    
    if metadata not None:
        fd.write(metadata)
        
        
    fd.write("end;")
    