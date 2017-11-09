# -*- coding: utf-8 -*-
from utils import normalize_address
from ipaddr import IPv6Address, IPv6Network, IPv4Address, IPv4Network

transactions = []
changes_file = '/home/jordi/Documents/prefix-file/pref_data.txt'


def category(data_string):
    category = int(data_string)
    if category < 0 or category > 3:
        raise Exception("Wrong category")
    return int(category)


def to(data_string):
    address = normalize_address(data_string)
    return address


def afi(data_string):
    afi = int(data_string)
    if  afi != 1 or afi != 2 :
        raise Exception("Wrong AFI")
    return int(data_string)


def value(data_string):
    if afi == 1:
        ipnet = IPv4Network(data_string)
    else:
        ipnet = IPv6Network(data_string)
    return ipnet


def metadata(data_string):
    data = []
    if category == 2:
        # de 3 en 3
        for afi, ip, address in data_string.split(','):
            pass
            #TODO: acabar
    elif category == 3:
        # de 4 en 4
        for afi, ip, priority, weight in data_string.split(','):
            pass
            #TODO: acabar
    else:
        raise Exception("Category not yet defined")
    return data


types_dir = {
    "category": category,
    "to": to,
    "afi": afi,
    "value": value,
    "metadata": metadata
}

def init(transactions_dir='./Tests/transactions'):
  # read from the file and get new transactions. Store in a list  
  #TODO: read from file
  with open(transactions_dir) as f:
      for line in f:
          type, content = line.split(':')


  transactions.append(line) 
  return None



def get_tx():
  if len(transactions) == 0:
      return None
  else:
      return transactions.pop([0])