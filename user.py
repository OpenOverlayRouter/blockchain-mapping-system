# -*- coding: utf-8 -*-


transactions = []
changes_file = '/home/jordi/Documents/prefix-file/pref_data.txt'

def init():
  # read from the file and get new transactions. Store in a list  
  #TODO: read from file  
  transactions.append(line) 
  return None



def get_tx():
  if len(transactions) == 0:
      return None
  else:
      return transactions.pop([0])