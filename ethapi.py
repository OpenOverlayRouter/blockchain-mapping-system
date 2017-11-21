import urllib, json
from xml.dom import minidom

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

def get_hash_from_NIST(timestamp):
	url = "https://beacon.nist.gov/rest/record/previous/"+str(timestamp)
	response = urllib.urlopen(url)
	xml_data = minidom.parse(response)
	for element in xml_data.getElementsByTagName('outputValue'):
		return element.firstChild.nodeValue
	#return "0ED51848CD85288B649663965264B32F470DB6A50A981E365E0F8EAA25DF926A98FF1055733F19EB92BA6E12088E83ADE060BA840D53E599DE6B9925889B07DB"