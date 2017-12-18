# -*- coding: utf-8 -*-
from utils import normalize_address
from ipaddr import IPv6Address, IPv6Network, IPv4Address, IPv4Network
from transactions import Transaction
from chain_service import ChainService
from keystore import Keystore

transactions = []
changes_file = '/home/jordi/Documents/prefix-file/pref_data.txt'

########################################################################################################################
#                                               USER INPUT DATA FORMAT:                                                #
#                                                                                                                      #
#               VARIABLE;DATA,DATA,DATA                                                                                #
#                                                                                                                      #
#               VARIABLE can be any of the following: category, to, afi, value, metadata                               #
#               VARIABLE MUST be read in the following order:                                                          #
#                                   · category must be read before metadata                                            #
#                                   · afi must be read before value                                                    #
#                                                                                                                      #
#                           category                                                                                   #
#                           to                                                                                         #
#                           afi                                                                                        #
#                           from                                                                                       #
#                           value                                                                                      #
#                           metadata                                                                                   #
#                           end  ->  this field indicates the end of the data of the transaction                       #
#                                                                                                                      #
#               DATA is the data related to the field indicated by VARIABLE                                            #
#               If the current field is metadata, each one of its variables (priority, weight, @IP, etc)               #
#               has to be separated with commas (',') and without blank spaces                                         #
#                                                                                                                      #
########################################################################################################################


class Parser():

    def __init__(self):
        self.transactions = []


    # sets the "category2 field of the data_buffer dict with the data in the data_string
    def category(self, data_string, data_buffer):
        category = int(data_string)
        if category < 0 or category > 3:
            raise Exception("Wrong category")
        data_buffer["category"] = int(category)

    # sets the "to" field of the data_buffer dict with the data in the data_string
    def to(self, data_string, data_buffer):
        address = normalize_address(data_string)
        data_buffer["to"] = address

    # sets the "afi" field of the data_buffer dict with the data in the data_string
    def afi(self, data_string, data_buffer):
        afi = int(data_string)
        if afi != 1 and afi != 2:
            raise Exception("Wrong AFI")
        data_buffer["afi"] = int(data_string)

    # sets the "value" field of the data_buffer dict with the data in the data_string
    def value(self, data_string, data_buffer):
        data_buffer["value"] = data_string

    # sets the "from" field of the data_buffer dict with the data in the data_string
    def frm(self, data_string, data_buffer):
        data_buffer["from"] = data_string

    # sets the "metadata" field of the data_buffer dict with the data in the data_string
    def metadata(self, data_string, data_buffer):
        data_buffer["metadata"] = []
        data = data_string.split(',')
        it = iter(data)
        if data_buffer["category"] == 2:
            if len(data)%3 != 0:
                raise Exception("metadata of a transaction with category 2 is not multiple of 3")
            # de 3 en 3
            for afi, ip, address in zip(*[iter(data)]*3):
                data_buffer["metadata"].append(int(afi))
                if int(afi) == 1 or int(afi) == 2:
                    data_buffer["metadata"].append(str(ip))
                else:
                    raise Exception("Incorrect AFI in metadata")
                data_buffer["metadata"].append(normalize_address(str(address)))
        elif data_buffer["category"] == 3:
            if len(data)%4 != 0:
                raise Exception("metadata of a transaction with category 3 is not multiple of 4")
            # de 4 en 4
            for afi, ip, priority, weight in zip(*[iter(data)]*4):
                data_buffer["metadata"].append(int(afi))
                if int(afi) == 1 or int(afi) == 2:
                    data_buffer["metadata"].append(str(ip))
                else:
                    raise Exception("Incorrect AFI in metadata")
                data_buffer["metadata"].appned(int(priority))
                data_buffer["metadata"].append(int(weight))
        else:
            raise Exception("Category not yet defined")

    types_dir = {
        "category": category,
        "to": to,
        "from": frm,
        "afi": afi,
        "value": value,
        "metadata": metadata
    }

    # read from the file and get new transactions. Store in a list
    def read_transactions(self, transactions_dir='./transactions.txt'):
        buffers = []
        with open(transactions_dir) as f:
            data_buffer = {}
            for line in f:
                type, content = line.split(';')
                content = content.strip("\n")
                if type == "end":
                    if data_buffer.get("afi") is not None and data_buffer.get("category") is not None and \
                                    data_buffer.get("value") is not None and data_buffer.get("to") is not None:
                        buffers.append(data_buffer)
                        print("All necessary fields are filled. Adding one transaction...")
                    else:
                        raise Exception("One transaction contains errors.")
                    data_buffer = {}
                else:
                    self.types_dir[type](self, content, data_buffer)
        self.transactions = buffers

        #open(transactions_dir, 'w').close()  # to remove all contents of the txt file


    # returns the first transaction of the "transactions" list
    def get_tx(self):
        if len(self.transactions) == 0:
            return None
        else:
            tx = self.transactions[0]
            self.transactions.remove(tx)
            return tx

