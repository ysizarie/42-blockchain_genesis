import hashlib as hl
import json


def hasha256(string):
    return hl.sha256(string).hexdigest()


def hash_block(block):
    hashable_block = block.__dict__.copy()
    hashable_block['transactions'] = [tx.to_ordered_dict()
                                      for tx in hashable_block['transactions']]
    return hasha256(json.dumps(hashable_block, sort_keys=True).encode())
