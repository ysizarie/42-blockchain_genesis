# Custom
from Helpers.hash_utils import hash_block, hasha256
from wallet import Wallet


class Validation():
    """docstring for Validation"""
    @classmethod
    def verify_chain(cls, blockchain):
        for index, block in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Invalid proof_of_work value")
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance, check_balance=True):
        if check_balance:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_tx(transaction)
        return Wallet.verify_tx(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])

    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]
                     ) + str(last_hash) + str(proof)).encode()
        guess_hash = hasha256(guess)
        return guess_hash[0:2] == '00'
