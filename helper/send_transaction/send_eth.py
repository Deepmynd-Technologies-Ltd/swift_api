from web3 import Web3
from eth_account import Account
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

infura_url = f'https://mainnet.infura.io/v3/{settings.INFURA}'
web3 = Web3(Web3.HTTPProvider(infura_url))

def send_eth(req: SendTransactionDTO):
    try:
        account = Account.from_key(req.private_key)

        if not web3.is_address(req.to_address):
            raise ValueError("Invalid to_address")

        if account.address != req.from_address:
            raise ValueError("Private key does not match from_address")

        value = web3.to_wei(req.amount, 'ether')
        nonce = web3.eth.get_transaction_count(account.address)
        balance = web3.eth.get_balance(account.address)

        if value > balance:
            raise ValueError("Insufficient balance")

        transaction_params = {
            'to': req.to_address,
            'value': value,
            'nonce': nonce,
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
        }

        signed_tx = web3.eth.account.sign_transaction(transaction_params, req.private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.get_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash.hex(),
            "receipt": receipt,
            "gas_price": transaction_params["gasPrice"]
        }

    except Exception as ex:
        raise RuntimeError(f"ETH transfer failed: {ex}")
