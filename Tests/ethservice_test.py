from eth_service import ChainService
import transactions
import db

db = db.EphemDB()
service = ChainService(db)

transact = []
transact.append(transactions.Transaction(1, '', 1, 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transact.append(transactions.Transaction(2, '', 2, 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transact.append(transactions.Transaction(3, '', 3, 0, 'data', 1, 1, 1))


for i in range (0, len(transact)):
    service.add_transaction(transact[i])


print('add_block')
service.add_block()

print('checking if exists block 0')
if service.get_block_in_position_i(0) is not None:
    print ('exists')
else:
    print ('not exists')
