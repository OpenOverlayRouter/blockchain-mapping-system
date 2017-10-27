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
	eth_hash_bits = from_hex_to_bits(eth_hash,256)

	# Get Nist hash
	timestamp = get_current_timestamp()
	nist_hash = get_hash_from_NIST(int(timestamp))
	nist_hash = hex(int(nist_hash.replace('L', '').zfill(8), 16))[:-1]
	nist_hash_bits = from_hex_to_bits(nist_hash,512)

	xor = long(eth_hash_bits,2)^long(nist_hash_bits,2)
	return from_long_to_bits(xor)

def from_hex_to_bits(h,nbits):
	return bin(int(h,16))[2:].zfill(nbits)

def from_long_to_bits(l):
	return "{0:b}".format(l)

res = get_random_hash()
print res