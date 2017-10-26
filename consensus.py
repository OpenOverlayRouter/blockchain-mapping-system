import time
import datetime
from ethapi import *

def get_hash_from_json_block(json_block):
	return json_block['result']['hash']

def get_current_timestamp():
	curDate = time.strftime("%x")
	curTime = time.strftime("%X")
	now = curDate+" "+curTime
	return time.mktime(datetime.datetime.strptime(now, "%m/%d/%y %H:%M:%S").timetuple())

last_block_number = get_last_block_number()
json_block = get_block_by_number(last_block_number)
print "Ethereum Hash: ",get_hash_from_json_block(json_block)


timestamp = get_current_timestamp()
hash = get_hash_from_NIST(int(timestamp))
hash = hex(int(hash.replace('L', '').zfill(8), 16))
print "NIST Hash: ",hash[:-1]
