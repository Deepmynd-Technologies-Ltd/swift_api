from web3 import Web3

from home.wallet_schema import SendTransactionDTO

# Connect to Binance Smart Chain RPC
web3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

def send_bnb(req: SendTransactionDTO):
    try:
        account = web3.eth.account.from_key(req.private_key)

        if not web3.is_address(req.to_address):
            raise Exception("Invalid Address")

        if account.address != req.from_address:
            raise Exception("Incorrect address")

        amount_wei = web3.to_wei(req.amount, 'ether')
        nonce = web3.eth.get_transaction_count(account.address)
        balance = web3.eth.get_balance(account.address)

        if amount_wei > balance:
            raise Exception("Insufficient Balance")

        trx = {
            'to': req.to_address,
            'value': amount_wei,
            'nonce': nonce,
            'gas': 21000,  # Correct minimum for basic transfer
            'gasPrice': web3.eth.gas_price,
            "chainId": 56
        }

        signed_tx = web3.eth.account.sign_transaction(trx, req.private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.get_transaction_receipt(tx_hash)

        return receipt, trx["gasPrice"]

    except Exception as ex:
        raise RuntimeError(f"{ex}")
