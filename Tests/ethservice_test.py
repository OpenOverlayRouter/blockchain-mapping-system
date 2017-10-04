from eth_service import ChainService
import transactions
import db

db = db.EphemDB()
service = ChainService(db)

transactions = []
transactions.append(transactions.Transaction(1, '', '', 1, 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transactions.append(transactions.Transaction(2, '', '', 2, 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transactions.append(transactions.Transaction(3, '', '', 3, 0, 'data', 1, 1, 1))


for i in range (0, len(transactions)):
    service.add_transaction(transactions[i])

for i in range (0, len(transactions)):
    if service.get_transaction_i(i) is not None:
        print('transaction found in index' + str(i))

print('add_block')
service.add_block()

print('checking if exists block 0')
if service.get_block_in_position_i(0) is not None:
    print ('exists')
else:
    print ('not exists')
