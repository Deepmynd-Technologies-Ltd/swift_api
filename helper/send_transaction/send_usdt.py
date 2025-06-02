from web3 import Web3
from eth_account import Account
from home.wallet_schema import SendTransactionDTO

def send_usdt(req: SendTransactionDTO):
    try:
        # Connect to BSC node
        rpc_url = "https://bsc-dataseed.binance.org/"
        web3 = Web3(Web3.HTTPProvider(rpc_url))

        if not web3.is_connected():
            raise Exception("Failed to connect to Binance Smart Chain node.")

        # Sender address from the private key
        sender_address = web3.eth.account.from_key(req.private_key).address

        if sender_address.lower() != req.from_address.lower():
            raise Exception("Invalid address: from_address does not match private key.")

        # USDT Contract ABI (includes balanceOf and transfer)
        abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]

        # USDT BEP-20 Contract address on BSC
        usdt_contract_address = "0x55d398326f99059fF775485246999027B3197955"
        token_contract = web3.eth.contract(address=Web3.to_checksum_address(usdt_contract_address), abi=abi)

        # Convert amount to smallest unit (18 decimals for BEP-20 USDT)
        amount_in_wei = int(req.amount * 1e18)

        # Check balance
        balance = token_contract.functions.balanceOf(sender_address).call()
        print(f"[DEBUG] Wallet balance: {balance / 1e18} USDT | Attempting to send: {req.amount} USDT")
        if balance < amount_in_wei:
            raise Exception("Insufficient balance")

        # Build the transaction
        nonce = web3.eth.get_transaction_count(sender_address)
        gas_price = web3.eth.gas_price
        gas_limit = 100000  # Adjust as needed

        transaction = token_contract.functions.transfer(
            Web3.to_checksum_address(req.to_address),
            amount_in_wei
        ).build_transaction({
            'chainId': 56,  # Binance Smart Chain Mainnet
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce
        })

        # Sign and send
        signed_tx = web3.eth.account.sign_transaction(transaction, req.private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return web3.to_hex(tx_hash)

    except Exception as ex:
        raise RuntimeError(f"USDT transfer failed: {ex}")
