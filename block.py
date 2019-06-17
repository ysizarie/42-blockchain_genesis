from time import time
from Helpers.printable import Printable


class Block(Printable):
    """docstring for Block"""

    def __init__(self, index, previous_hash, transactions, proof, timestamp=time()):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.proof = proof
        self.timestamp = timestamp
