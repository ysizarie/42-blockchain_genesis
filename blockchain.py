from functools import reduce
from collections import OrderedDict
# Custom
from Helpers.hash_utils import hash_block
from block import Block
from transaction import Transaction
from Helpers.validation import Validation
from wallet import Wallet
# ######
import hashlib as hl
import json
import pickle


MINING_REWARD = 1


class Blockchain():
    """docstring for Blockchain"""

    def __init__(self, host_node_id):
        # Genesis block initialization.
        genesis_block = Block(0, '', [], 0, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.load_data()
        self.host_node = host_node_id

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        try:
            with open('blockchain.txt', mode='r') as fd:
                content = fd.readlines()
                blockchain = json.loads(content[0][:-1])
                new_blockchain = []
                new_transactions = []
                for block in blockchain:
                    txs = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                           for tx in block['transactions']]
                    new_block = Block(
                        block['index'], block['previous_hash'], txs, block['proof'], block['timestamp'])
                    new_blockchain.append(new_block)
                self.chain = new_blockchain
                self.__open_transactions = json.loads(content[1])
                for tx in self.__open_transactions:
                    new_transaction = Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    new_transactions.append(new_transaction)
                self.__open_transactions = new_transactions
        except (IOError, IndexError):
            print('Dump file not found.')

    def save_data(self):
        try:
            with open('blockchain.txt', mode='w') as fd:
                savable_blockchain = [block.__dict__ for block in [Block(blk.index, blk.previous_hash, [
                                                                         tx.__dict__ for tx in blk.transactions], blk.proof, blk.timestamp) for blk in self.__chain]]
                savable_transactions = [
                    tx.__dict__ for tx in self.__open_transactions]
                fd.write(json.dumps(savable_blockchain))
                fd.write("\n")
                fd.write(json.dumps(savable_transactions))
        except (IOError):
            print('Saving failed.')

    def get_last_block(self):
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def get_balance(self):
        if self.host_node is None:
            return None
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == self.host_node] for block in self.__chain]
        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == self.host_node] for block in self.__chain]
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions if tx.sender == self.host_node]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(lambda tx_sum, val: tx_sum + sum(val)
                             if len(val) > 0 else tx_sum + 0, tx_sender, 0)
        amount_claimed = reduce(lambda tx_sum, val: tx_sum + sum(val)
                                if len(val) > 0 else tx_sum + 0, tx_recipient, 0)
        return amount_claimed - amount_sent

    def add_tx_val(self, tx_amount):

        if len(self.__chain) > 0:
            last_block = self.get_last_block()
        else:
            last_block = [0]
        self.__chain.append([last_block, tx_amount])

    def add_transaction(self, recipient, sender, signature, amount=1.0):
        if self.host_node is None:
            return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Validation.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            return True
        return False

    def mine_block(self):
        if self.host_node is None:
            return None
        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        reward_tx = Transaction('SYSTEM', self.host_node, '', MINING_REWARD)
        copy_transactions = self.__open_transactions[:]
        for tx in copy_transactions:
            if not Wallet.verify_tx(tx):
                return None
        copy_transactions.append(reward_tx)
        block = Block(len(self.__chain), hashed_block,
                      copy_transactions, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        return block

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        while not Validation.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof
