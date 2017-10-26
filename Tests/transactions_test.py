import utils
from transactions import Transaction
import rlp

#key = utils.random_privkey()
key = '2ff2ea218ea9ee91ddd651065e63551ee14cf82ec70a2ca0fa71923da10dd97c'
addr = utils.privtoaddr(key)
print "SENDER:", addr.encode('hex')

# Category 1&2
tx = Transaction(5,1,'54450450e24286143a35686ad77a7c851ada01a0', 333, '192.152.0.0/16')

# Category 2
tx = Transaction(5,2,'54450450e24286143a35686ad77a7c851ada01a0', 555, '192.152.0.0/16', 
    ['1.1.1.1', '54dbb737eac5007103e729e9ab7ce64a6850a310',
     '2.2.2.2', '89b44e4d3c81ede05d0f5de8d1a68f754d73d997',
     '3.3.3.3', '3a1e02d9ea25349c47fe2e94f4265cd261c5c7ca'])

# Category 3
tx = Transaction(5,3,'54450450e24286143a35686ad77a7c851ada01a0', 555, '192.152.0.0/16', 
    ['4.4.4.4', 20, 230,
     '5.5.5.5', 45, 50])

tx.sign(key)
print "Tx ID", tx.hash.encode('hex')
#print tx.ip_network
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

'''
rawtx = ('f86d05039454450450e24286143a35686ad77a7c851ada01a0820'
        '22b85c098000010c884010101011481FF801ba0a7902f2e457c08'
        '69692c1cb3467cdc8afe7f153e332979346fcef7627e98c25fa02'
        'c9203e4e4547d85a6268f5660e8fdd79de9892b347a05d03a8b40'
        '318f8745f5')
tx2 = rlp.decode(rawtx.decode('hex'), Transaction)
print '\n', tx2.to_dict(), '\n'
'''
