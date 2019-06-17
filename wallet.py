from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii


class Wallet():
    """docstring for Wallet"""

    def __init__(self):
        self.private_key = None
        self.public_key = None

    def generate_keys(self):
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'), binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii'))

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def export_keys(self):
        if self.public_key is not None and self.private_key is not None:
            try:
                with open('wallet.txt', mode='w') as fd:
                    fd.write(self.public_key)
                    fd.write('\n')
                    fd.write(self.private_key)
                    return True
            except (IOError, IndexError):
                return False

    def import_keys(self):
        try:
            with open('wallet.txt', mode='r') as fd:
                keys = fd.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
                return True
        except (IOError, IndexError):
            return False

    def sign_tx(self, sender, recipient, amount):
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        hasher = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(hasher)
        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_tx(transaction):
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        validator = PKCS1_v1_5.new(public_key)
        hasher = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8'))
        return validator.verify(hasher, binascii.unhexlify(transaction.signature))
