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

def get_random_hash():
	# Get Ethereum hash
	last_block_number = get_last_block_number()
	json_block = get_block_by_number(last_block_number)
	eth_hash = get_hash_from_json_block(json_block)

	# Get Nist hash
	timestamp = get_current_timestamp()
	nist_hash = get_hash_from_NIST(int(timestamp))
	nist_hash = hex(int(nist_hash.replace('L', '').zfill(8), 16))[:-1]

	return int(eth_hash,0)^int(nist_hash,0)

print get_random_hash()
