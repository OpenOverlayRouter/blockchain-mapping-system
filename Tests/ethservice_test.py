from eth_service import ChainService
import transactiondb
import db

db = db.EphemDB()
service = ChainService(db)

transactions = []
transactions.append(transactiondb.Transaction(1, '', '', 1, 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transactions.append(transactiondb.Transaction(2, '', '', 2, 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transactions.append(transactiondb.Transaction(3, '', '', 3, 0, 'data', 1, 1, 1))


for i in range (0, len(transactions)):
    service.add_transaction(transactions[i])

for i in range (0, len(transactions)):
    print(service.get_transaction_i(i))
