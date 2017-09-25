import eth_service
import transactiondb
import db

db = db.OverlayDB(db)
service = eth_service.ChainService(db)

transactions = []
transactions.append(transactiondb.Transaction(1, '0x000', '0x001', 1, 0, 'data', 'v', 'r', 's'))
transactions.append(transactiondb.Transaction(2, '0x001', '0x002', 2, 0, 'data', 'v', 'r', 's'))
transactions.append(transactiondb.Transaction(3, '0x002', '0x003', 3, 0, 'data', 'v', 'r', 's'))

service.newBlock() #create empty block

for i in range (0, len(transactions)):
    service.addTransaction(transactions[i])

for i in range (0, len(transactions)):
    print(service.getTransactioni(i))