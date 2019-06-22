from time import time
from Helpers.printable import Printable


class Block(Printable):
    """Block class is used to represent a block part of the blockchain."""

    def __init__(self, index, previous_hash, transactions, proof, timestamp=time()):
        """Constructor of the block class.

        Args:
            index (int): index of a block in tho blockchain.
            previous_hash (hash): hash of previous block if it's not a genesis
            transactions (list): list of transactions added by miners.
            proof (int): Proof of Work value.
            timestamp (int, optional): block creation time.
        """
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.proof = proof
        self.timestamp = timestamp
