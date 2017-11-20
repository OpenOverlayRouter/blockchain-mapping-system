import time
import datetime
import ipaddress
from ethapi import *

IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128

class Consensus():

	def __init__(self):
		self.next_signer = None
		self.last_timestamp = 0
		self.ips = []

	def get_next_signer(self):
		return self.next_signer

	def calculate_next_signer(self, ips, timestamp):
		if timestamp == self.last_timestamp:
			# Check that there is a new block in 30 seconds
			current_timestamp = get_timestamp()
			if (current_timestamp-timestamp) >= 30:
				timestamp = timestamp+30
				new_signer = who_signs("IPv4", timestamp)
			else:
				new_signer = None
				# If the timestamp is the same, we need to wait until NIST or Ethereum
				# hashes changes. So we put next_signer to None until we get a
				# valid signer. i.e. adding 30s to timestamp
		else:
			new_signer= who_signs("IPv4", timestamp)
		self.next_signer = new_signer
		self.last_timestamp = timestamp
		self.ips = ips

	def amISigner(self, ips):
		# TODO: calcular 30 segons desde el timestamp (self.timestamp?)
		self.ips = ips
		if self.next_signer in self.ips:
			return true
		return false

# Returns the HASH of a block
def get_hash_from_json_block(json_block):
	return json_block['result']['hash']

# Returns the Timestamp of a block
def get_timestamp_from_json_block(json_block):
	return json_block['result']['timestamp']

def get_timestamp():
	curDate = time.strftime("%x")
	curTime = time.strftime("%X")
	now = curDate+" "+curTime
	return time.mktime(datetime.datetime.strptime(now, "%m/%d/%y %H:%M:%S").timetuple())

# Returns the timestamp of the last block
def get_last_block_timestamp():
	return get_current_timestamp()

# Converts from hexa format to bits format
def from_hex_to_bits(h,nbits):
	return bin(int(h,16))[2:].zfill(nbits)

# Converts from long format to bits format
def from_long_to_bits(l):
	res = "{0:b}".format(l)
	while len(res) < 512:
		res = "0"+res
	return res

# Converts from hexadecimal format to int
def from_hex_to_int(h):
	return int(h,0)

# Substract decr times to an hexa value
def sub_to_hex(h,decr):
	return "0x"+'{:x}'.format(int(h,0)-decr)

# Returns the block that was in the chain at timestamp time
def get_block_from_timestamp(last_block_number,timestamp):
	block_number = last_block_number
	json_block = get_block_by_number(last_block_number)
	block_timestamp = from_hex_to_int(get_timestamp_from_json_block(json_block))
	while (timestamp < block_timestamp):
		#print block_timestamp
		block_number = sub_to_hex(block_number,1)
		json_block = get_block_by_number(block_number)
		block_timestamp = from_hex_to_int(get_timestamp_from_json_block(json_block))
	return json_block

# Returns a random HASH mixing NIST and ETHEREUM HASH block
def get_random_hash(timestamp):
	# Get timestamp to work with
	#timestamp = get_timestamp()

	# Get Ethereum hash
	last_block_number = get_last_block_number()
	selected_block_number = get_block_from_timestamp(last_block_number,timestamp)
	eth_hash = get_hash_from_json_block(selected_block_number)
	eth_hash_bits = from_hex_to_bits(eth_hash,256)

	# Get Nist hash
	nist_hash = get_hash_from_NIST(int(timestamp))
	nist_hash = hex(int(nist_hash.replace('L', '').zfill(8), 16))[:-1]
	nist_hash_bits = from_hex_to_bits(nist_hash,512)

	# Mix both hashes
	xor = long(eth_hash_bits,2)^long(nist_hash_bits,2)
	return from_long_to_bits(xor)

# Returns the IP Address in a readable format
def formalize_IP(IP_bit_list):
	ip = int(IP_bit_list,2)
	return ipaddress.ip_address(ip)

# Given a random HASH, returns the selected address in a list
def consensus_for_IPv6(hash):
	ngroup = len(hash)/IPv6_PREFIX_LENGTH
	address = ""
	for i in range (0,len(hash),ngroup):
		ini_xor = int(hash[i],2)
		for j in range (i+1,i+ngroup):
			ini_xor = ini_xor^int(hash[j],2)
		address = address+str(ini_xor)

	return address

# Given a random HASH, returns the selected address in a list
def consensus_for_IPv4(hash):
	ngroup = len(hash)/IPv4_PREFIX_LENGTH
	address = ""
	for i in range (0,len(hash),ngroup):
		ini_xor = int(hash[i],2)
		for j in range (i,i+ngroup):
			ini_xor = ini_xor^int(hash[j],2)
		address = address+str(ini_xor)

	return address

# Given the protocol type, returns the selected address in the correct format
def who_signs(protocol, timestamp):
	hash = get_random_hash(timestamp)
	if protocol == "IPv6":
		return formalize_IP(consensus_for_IPv6(hash))
	else:
		return formalize_IP(consensus_for_IPv4(hash))

#print who_signs("IPv4")
#TODO:
	#signer_IP = who_signs(Protocol)
	#if balance.in_own_ips(signer_IP):
	#	block = chain.create_block(coinbase)
	#	chain.add_block(block)
	#	broadcast_message("new_block")
	#else:
	#	received = true
	#	while(not new_block_message_received in 60 seconds)
	#	received = false
	#if not received:
	#	consensus()