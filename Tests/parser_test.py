from user import Parser

p = Parser()
print "leyendo"
p.read_transactions(transactions_dir='./transactions.txt')
t = p.get_tx()
print t
print t["to"].encode('HEX')
print t["from"].encode('HEX')
print "ya leido"