import time
import datetime
import hashlib
import logging
import logger
from ethapi import *
from netaddr import IPAddress, IPNetwork, IPSet

IPv4_PREFIX_LENGTH = 32
IPv6_PREFIX_LENGTH = 128
ETH_BPS = 14

logger.setup_custom_logger('Consensus')
consensusLog = logging.getLogger('Consensus')

class Consensus():

	def __init__(self):
		self.next_signer = None
		self.last_timestamp = 0
		self.ips = []
		self.logger = logging.getLogger('Consensus')
		self.found_in_chain = False

	def get_next_signer(self):
		return self.next_signer

	def calculate_next_signer(self, ips, timestamp, block_number):
		if block_number % 2 != 0: # block_number is the previous one, so if it is even, next should be IPv6
			protocol = "IPv4"
		else:
			protocol = "IPv6"
		if timestamp == self.last_timestamp and self.found_in_chain:
			# Check that there is a new block in 60 seconds
			current_timestamp = get_timestamp()
			if (current_timestamp-timestamp) >= 30:
				timestamp = timestamp+30
				new_signer, found_in_chain = who_signs(protocol, timestamp)
			else:
				new_signer = None
				found_in_chain = False
				# If the timestamp is the same, we need to wait until NIST or Ethereum
				# hashes changes. So we put next_signer to None until we get a
				# valid signer. i.e. adding 30s to timestamp
		else:
			new_signer, found_in_chain = who_signs(protocol, timestamp)
		self.next_signer = new_signer
		self.last_timestamp = timestamp
		self.ips = ips
		self.found_in_chain = found_in_chain

	def amISigner(self, ips, block_number):
		if self.next_signer == None: 
			return False, None
		self.ips = ips
		ip_next_signer = IPAddress(self.next_signer)
		if block_number % 2 != 0:
			f = lambda x: x.version == 4
		else:
			f = lambda x: x.version == 6
		if ip_next_signer in IPSet(filter(f, ips.iter_cidrs())):
			return True, self.next_signer
		return False, self.next_signer


# Returns the HASH of a block
def get_hash_from_json_block(json_block):
	return json_block['result']['hash']

# Returns the Timestamp of a block
def get_timestamp_from_json_block(json_block):
	if json_block['result'] == None: 
		consensusLog.error('No timestamp in block')
		return 0x00
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

# Add sum times to an hexa value
def add_to_hex(h,sum):
	return "0x"+'{:x}'.format(int(h,0)+sum)

# Returns the block that was in the chain at timestamp time
def get_block_from_timestamp(last_block_number,timestamp):
	found = False
	block_number = last_block_number
	json_block = get_block_by_number(last_block_number)
	block_timestamp = from_hex_to_int(get_timestamp_from_json_block(json_block))

	if timestamp >= block_timestamp:
		json_block = None
	else:
		while not found:
			consensusLog.info('Searching old block timestamp')
			#print "Consensus: Searching old block timestamp"
			if timestamp < block_timestamp:
				if (block_timestamp-timestamp)/ETH_BPS >= 14:
					variance = int((block_timestamp-timestamp)/ETH_BPS)
					block_number = sub_to_hex(block_number,variance)
					json_block = get_block_by_number(block_number)
					block_timestamp = from_hex_to_int(get_timestamp_from_json_block(json_block))
				else:
					candidate_block_number = sub_to_hex(block_number,1)
					candidate_json_block = get_block_by_number(candidate_block_number)
					candidate_timestamp = from_hex_to_int(get_timestamp_from_json_block(candidate_json_block))
					while candidate_timestamp > timestamp:
						consensusLog.info('Block timestamp is close...')
						#print "Consensus: block timestamp is close..."
						candidate_block_number = sub_to_hex(candidate_block_number,1)
						candidate_json_block = get_block_by_number(candidate_block_number)
						candidate_timestamp = from_hex_to_int(get_timestamp_from_json_block(candidate_json_block))
					json_block = candidate_json_block
					found = True
					consensusLog.debug('Candidate: %s', candidate_block_number)
					#print "CANDIDATE: ", candidate_block_number
			elif block_timestamp < timestamp:
				if (timestamp-block_timestamp)/ETH_BPS >= 14:
					variance = int((timestamp-block_timestamp)/ETH_BPS)
					block_number = add_to_hex(block_number,variance)
					json_block = get_block_by_number(block_number)
					block_timestamp = from_hex_to_int(get_timestamp_from_json_block(json_block))
				else:
					candidate_block_number = add_to_hex(block_number,1)
					candidate_json_block = get_block_by_number(candidate_block_number)
					candidate_timestamp = from_hex_to_int(get_timestamp_from_json_block(candidate_json_block))
					while candidate_timestamp < timestamp:
						consensusLog.info('Block timestamp is close...')
						#print "Consensus: block timestamp is close..."
						candidate_block_number = add_to_hex(candidate_block_number,1)
						candidate_json_block = get_block_by_number(candidate_block_number)
						candidate_timestamp = from_hex_to_int(get_timestamp_from_json_block(candidate_json_block))
					if candidate_timestamp == timestamp:
						json_block = candidate_json_block
					else:
						json_block = get_block_by_number(sub_to_hex(candidate_block_number,1))
						consensusLog.debug('Candidate Sub: %s', sub_to_hex(candidate_block_number,1))
						#print "Candidate: ", sub_to_hex(candidate_block_number,1)
					found = True
	consensusLog.debug('Timestamp for catching block: %s', timestamp)
	#print timestamp
	return json_block

# Returns a random HASH mixing NIST and ETHEREUM HASH block
def get_random_hash(timestamp):
	# Get Ethereum hash
	'''last_block_number = get_last_block_number()
	selected_block_number = get_block_from_timestamp(last_block_number,timestamp)
	if selected_block_number == None:
		#print "Consensus: No new ETH block yet, waiting for Ethereum chain..."
		consensusLog.info('No new ETH block yet, waiting for Ethereum chain...')
		return None, False
	#print "Consensus: New block found"
	consensusLog.info('New block fund on Ethereum chain')
	eth_hash = get_hash_from_json_block(selected_block_number)
	eth_hash_bits = from_hex_to_bits(eth_hash,256)'''

	# Get Nist hash
	nist_hash = get_hash_from_NIST(int(timestamp))
	if nist_hash == None:
		consensusLog.info('No new NIST hash yet, waiting for it...')
		return None, False
	consensusLog.info('New NIST hash found...')
	nist_hash = hex(int(nist_hash.replace('L', '').zfill(8), 16))[:-1]
	nist_hash_bits = from_hex_to_bits(nist_hash,512)

	# Mix both hashes
	#xor = long(eth_hash_bits+eth_hash_bits,2)^long(nist_hash_bits,2)
	xor = long(nist_hash_bits,2)
	return from_long_to_bits(xor), True

# Returns the IP Address in a readable format
def formalize_IP(IP_bit_list):
  ip = int(IP_bit_list,2)
  return IPAddress(ip)

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

def extractor(hash_string):
	new_hash = hashlib.sha256(hash_string).hexdigest()
	return from_hex_to_bits(new_hash,256)

# Given the protocol type, returns the selected address in the correct format
def who_signs(protocol, timestamp):
	hash_res, found_in_chain = get_random_hash(timestamp)
	if hash_res == None:
		return None, found_in_chain
	else:
		entropy_hash = extractor(hash_res)
		if protocol == "IPv6":
			return formalize_IP(consensus_for_IPv6(entropy_hash)), found_in_chain
		else:
			return formalize_IP(consensus_for_IPv4(entropy_hash)), found_in_chain
