import utils
from transactions import Transaction
import rlp

#key = utils.random_privkey()
key = '2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c'
addr = utils.privtoaddr(key)
print "SENDER:", addr.encode('hex')

# Category 1&2

#tx = Transaction(5,1,'54450450e24286143a35686ad77a7c851ada01a0', 1, '192.152.0.0/16')
#tx = Transaction(5,1,'54450450e24286143a35686ad77a7c851ada01a0', 2, '2001:db8::1/16')

# Category 2

'''tx = Transaction(5,2,'54450450e24286143a35686ad77a7c851ada01a0', 1, '192.152.0.0/16', 
    [1, '1.1.1.1', '54dbb737eac5007103e729e9ab7ce64a6850a310',
     1, '2.2.2.2', '89b44e4d3c81ede05d0f5de8d1a68f754d73d997',
     2, '2001:db8:a0b:12f0::1', '3a1e02d9ea25349c47fe2e94f4265cd261c5c7ca'])'''

tx = Transaction(5,2,'54450450e24286143a35686ad77a7c851ada01a0', 2, '2001:db8::1/16', 
    [1, '1.1.1.1', '54dbb737eac5007103e729e9ab7ce64a6850a310',
     2, '2001:cdba::3257:9652', '89b44e4d3c81ede05d0f5de8d1a68f754d73d997',
     1, '3.3.3.3', '3a1e02d9ea25349c47fe2e94f4265cd261c5c7ca'])

# Category 3
'''tx = Transaction(5,3,'54450450e24286143a35686ad77a7c851ada01a0', 1, '192.152.0.0/16', 
    [2, '2001:cdba:9abc:5678::', 20, 230,
     1, '5.5.5.5', 45, 50])'''

'''tx = Transaction(5,3,'54450450e24286143a35686ad77a7c851ada01a0', 2, '2001:db8::1/16', 
    [2, '2001:cdba:9abc:5678::', 20, 230])'''

tx.sign(key)
print "Tx ID", tx.hash.encode('hex')
print tx.ip_network
#print utils.ip_to_bytes('192.152.0.0/16').encode('hex')
assert tx.sender == addr
print "Tx Sender OK" 
assert tx.v in (27, 28)
print "V OK"
#print tx.metadata
print tx.to_dict()
rawtx = rlp.encode(tx).encode('hex')
print '\n', rawtx, '\n'
tx2 = rlp.decode(rawtx.decode('hex'), Transaction)
#print tx2.sender.encode('hex')
print tx2.to_dict()
assert rlp.encode(tx).encode('hex') == rlp.encode(tx2).encode('hex')
print "Tx Encode = Tx Decode: OK"


'''rawtx = ('f8cd05029454450450e24286143a35686ad77a7c851ada01a00291'
         '20010db800000000000000000000000110f85d0184010101019454'
         'dbb737eac5007103e729e9ab7ce64a6850a31002902001cdba0000'
         '000000000000325796529489b44e4d3c81ede05d0f5de8d1a68f75'
         '4d73d997018403030303943a1e02d9ea25349c47fe2e94f4265cd2'
         '61c5c7ca801ca047a05dcbc30b8cc7b14510c2b9e92364bab43ee7'
         'a317c0681a26f5136ccbe0aaa06bfd3b1751e4327095a85e93edce'
         'beb3266b7dca59369729cee2bd482e9ed3f3')
tx2 = rlp.decode(rawtx.decode('hex'), Transaction)'''
#print '\n', tx2.to_dict(), '\n' 

