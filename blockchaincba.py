# -*- coding: utf-8 -*-

import p2p
import consensus
import chain_service
import user
import oor


def init():
    p2p.init()
    oor.init()
    user.init()
    myIPs = chain_service.init()
    consensus.init(myIPs)
    
def run():
    
  end = 0
 
  while(not end):
   
   #Process a block
    block = p2p.get_block()
    if block is not None:
      signer = consensus.get_next_signer()
      res = chain_service.validate_block(block,signer)
      if res:
        # correct block
        myIPs = chain_service.add_block(block)
        consensus.calculate_next_signer(myIPs)
        p2p.broadcast_block(block)
      else:
        #reset consensus alg
        consensus.calculate_next_signer(None)
    
    #Process transactions from the network
    tx_ext = p2p.get_tx()
    if tx_ext is not None:    
      res = chain_service.validate_tx(tx_ext)
      if res:
        #correct tx
        chain_service.add_to_pool(tx_ext)
        p2p.broadcast_tx(tx_ext)
      #check if there are more transactions to process
      while (tx_ext.more):
        tx_ext = p2p.get_tx()
        res = chain_service.validate_tx(tx_ext)
        if res:
         #correct tx
          chain_service.add_to_pool(tx_ext)
          p2p.broadcast_tx(tx_ext)

    #Check if the node has to sign the next block
    sign = consensus.amIsinger(myIPs)
    if sign.me is True:
      new_block = chain_service.create_block(sign.signer)
      p2p.broadcast_block(new_block)

    #Process transactions from the user    
    tx_int = user.get_tx()
    if tx_int is not None:
      res = chain_service.validate_tx(tx_int)
      if res:
        #correct tx
        chain_service.add_to_pool(tx_int)
        p2p.broadcast_tx(tx_int)
     
    #answer queries from OOR     
    query = oor.get_query()
    if query is not None:
      info = chain_service.query_eid(query)
      oor.send(info)


if __name__ == "__main__":
    init()
    run()
    