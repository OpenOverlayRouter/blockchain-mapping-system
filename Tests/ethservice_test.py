import eth_service
import transactiondb
import db

db = db.OverlayDB(db)
service = eth_service.ChainService(db)

transactions = []
transactions.append(transactiondb.Transaction(1, '', '', 1, 0, 'data', 1, 1, 1)) #to be serializable, address can be empty and
transactions.append(transactiondb.Transaction(2, '', '', 2, 0, 'data', 1, 1, 1)) #v, r, s have to be integers
transactions.append(transactiondb.Transaction(3, '', '', 3, 0, 'data', 1, 1, 1))

service.newBlock() #create empty block

for i in range (0, len(transactions)):
    service.addTransaction(transactions[i])

for i in range (0, len(transactions)):
    print(service.getTransactioni(i))