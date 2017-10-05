from eth_service import ChainService
import transactions
import db


service = ChainService()

transact = []
transact.append(transactions.Transaction(1, '', "192.168.9.1/28", 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transact.append(transactions.Transaction(2, '', "192.170.9.1/28", 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transact.append(transactions.Transaction(3, '', "192.172.9.1/28", 0, 'data', 1, 1, 1))


for i in range (0, len(transact)):
    service.add_transaction(transact[i])


#print('add_block')
#service.add_block()

print('checking if exists block 0')
if service.get_block_in_position_i(0) is not None:
    print ('exists')
else:
    print ('not exists')

print('checking if exists block 1')
if service.get_block_in_position_i(1) is not None:
    print ('exists')
else:
    print ('not exists')
