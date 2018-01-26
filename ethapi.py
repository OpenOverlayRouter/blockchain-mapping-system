import urllib, json
import errno
import time
from xml.dom import minidom
from socket import error as SocketError

def get_last_block_number():
	url = "https://api.etherscan.io/api?module=proxy&action=eth_blockNumber"
	response = urllib.urlopen(url)
	data = json.loads(response.read())
	block_number = data['result']
	return block_number

def get_block_by_number(block_number):
	url = "https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag="+block_number+"&boolean=true"
	response = urllib.urlopen(url)
	json_block = json.loads(response.read())
	return json_block

def get_hash_from_NIST_nist(timestamp):
	#url = "https://beacon.nist.gov/rest/record/previous/"+str(timestamp)
	url = "https://beacon.nist.gov/rest/record/"+str(timestamp)
	try:
		response = urllib.urlopen(url)
	except SocketError as e:
		if e.errno != errno.ECONNRESET:
			raise
		# Handle connection reset by peer
		time.sleep(1)
		return None
	if response.getcode() == 404:
		return None
	xml_data = minidom.parse(response)
	for element in xml_data.getElementsByTagName('outputValue'):
		return element.firstChild.nodeValue

def get_hash_from_NIST_eth_nist(timestamp):
	url = "https://beacon.nist.gov/rest/record/previous/"+str(timestamp)
	try:
		response = urllib.urlopen(url)
	except SocketError as e:
		if e.errno != errno.ECONNRESET:
			raise
		# Handle connection reset by peer
		time.sleep(1)
		return None
	if response.getcode() == 404:
		return None
	xml_data = minidom.parse(response)
	for element in xml_data.getElementsByTagName('outputValue'):
		return element.firstChild.nodeValue

def get_timestamp():
        curDate = time.strftime("%x")
        curTime = time.strftime("%X")
        now = curDate+" "+curTime
        return time.mktime(datetime.datetime.strptime(now, "%m/%d/%y %H:%M:%S").timetuple())