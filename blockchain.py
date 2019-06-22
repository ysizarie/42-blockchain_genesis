from functools import reduce
from Helpers.hash_utils import hash_block
from block import Block
from transaction import Transaction
from Helpers.validation import Validation
from wallet import Wallet
import json
import requests


MINING_REWARD = 1


class Blockchain():
    def __init__(self, public_key, node_id):
        # Genesis block initialization.
        genesis_block = Block(0, '', [], 0, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

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
            with open('blockchain_{}.txt'.format(self.node_id), mode='r') as fd:
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
                self.__open_transactions = json.loads(content[1][:-1])
                for tx in self.__open_transactions:
                    new_transaction = Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    new_transactions.append(new_transaction)
                self.__open_transactions = new_transactions
                self.__nodes = set(json.loads(content[2]))
        except (IOError, IndexError):
            print('Dump file not found.')

    def save_data(self):
        try:
            with open('blockchain_{}.txt'.format(self.node_id), mode='w') as fd:
                savable_blockchain = [block.__dict__ for block in [Block(blk.index, blk.previous_hash, [
                                                                         tx.__dict__ for tx in blk.transactions], blk.proof, blk.timestamp) for blk in self.__chain]]
                savable_transactions = [
                    tx.__dict__ for tx in self.__open_transactions]
                fd.write(json.dumps(savable_blockchain))
                fd.write("\n")
                fd.write(json.dumps(savable_transactions))
                fd.write("\n")
                fd.write(json.dumps(list(self.__nodes)))
        except (IOError):
            print('Saving failed.')

    def get_last_block(self):
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def get_balance(self, sender=None):
        if sender is None:
            if self.public_key is None:
                return None
            user = self.public_key
        else:
            user = sender
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == user] for block in self.__chain]
        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == user] for block in self.__chain]
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions if tx.sender == user]
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

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        # if self.public_key is None:
        #     return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Validation.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__nodes:
                    url = 'http://{}/broadcast_transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                                                 "sender": sender, "recipient": recipient, "amount": amount, "signature": signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print("Transaction declined, needs resolving.")
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def add_block(self, block):
        transactions = [Transaction(
            tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        valid_proof = Validation.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not valid_proof or not hashes_match:
            return False
        new_block = Block(block['index'], block['previous_hash'],
                          transactions, block['proof'], block['timestamp'])
        self.__chain.append(new_block)
        stored_tx = self.__open_transactions[:]
        for itx in block['transactions']:
            for optx in stored_tx:
                if optx.sender == itx['sender'] and optx.recipient == itx['recipient'] and optx.amount == itx['amount'] and optx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(optx)
                    except ValueError:
                        print("Item was already removed.")
        self.save_data()
        return True

    def mine_block(self):
        if self.public_key is None:
            return None
        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        reward_tx = Transaction('SYSTEM', self.public_key, '', MINING_REWARD)
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
        for node in self.__nodes:
            url = 'http://{}/broadcast_block'.format(node)
            new_block = block.__dict__.copy()
            new_block['transactions'] = [
                tx.__dict__ for tx in new_block['transactions']]
            try:
                response = requests.post(url, json={'block': new_block})
                if response.status_code == 400 or response.status_code == 500:
                    print("Block declined, needs resolving.")
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        while not Validation.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__nodes:
            url = "http://{}/chain".format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(
                    tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']],
                    block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Validation.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_node(self, node):
        self.__nodes.add(node)
        self.save_data()

    def remove_node(self, node):
        self.__nodes.discard(node)
        self.save_data()

    def get_nodes(self):
        return list(self.__nodes)[:]
