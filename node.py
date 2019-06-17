from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
from wallet import Wallet
import json
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.export_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Failed to save keys.'}
        return jsonify(response), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.import_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Failed to load keys.'}
        return jsonify(response), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance is not None:
        response = {
            'message': 'Fetched balance successfully.',
            'balance': balance
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Failed to load balance.',
            'wallet': wallet.public_key is not None
        }
        return jsonify(response), 500


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/transaction', methods=['POST'])
def add_tx():
    if wallet.public_key is None:
        response = {'message': 'Wallet not found.'}
        return jsonify(response), 400
    values = request.get_json()
    requirements = ['recipient', 'amount']
    if not values:
        response = {'message': 'Invalid Transaction.'}
        return jsonify(response), 400
    if not all(k in values for k in requirements):
        response = {'message': 'Not enough transaction values.'}
        return jsonify(response), 400
    if values['amount'] < 0 or values['amount'] > blockchain.get_balance():
        response = {'message': 'Invalid Transaction.'}
        return jsonify(response), 400
    signature = wallet.sign_tx(wallet.public_key, values['recipient'], values['amount'])
    success = blockchain.add_transaction(values['recipient'], wallet.public_key, signature, values['amount'])
    if success:
        response = {
            'message': 'Succeess.',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': values['recipient'],
                'signature': signature,
                'amount': values['amount']
            },
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Failed to create transaction.'}
        return jsonify(response), 500


@app.route('/transactions', methods=['GET'])
def get_transactions():
    txs = blockchain.get_transactions()
    dtxs = [tx.__dict__ for tx in txs]
    return jsonify(dtxs), 200


@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block is not None:
        dblock = block.__dict__.copy()
        dblock['transactions'] = [tx.__dict__ for tx in dblock['transactions']]
        response = {
            'message': 'Block mined successfully.',
            'wallet': dblock,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Failed To mine a new block.',
            'wallet': wallet.public_key is not None
        }
        return jsonify(response), 500


@app.route('/chain', methods=['GET'])
def get_chain():
    chain = blockchain.chain
    dchain = [block.__dict__.copy() for block in chain]
    for dblock in dchain:
        dblock['transactions'] = [tx.__dict__ for tx in dblock['transactions']]
    return jsonify(dchain), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
