from web3 import Web3
from eth_account import Account
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

# USDT Contract Details (ERC-20)
USDT_CONTRACT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  # Mainnet
USDT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

# Infura or another Ethereum provider
web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/' + settings.INFURA))

def send_usdt(req: SendTransactionDTO):
    try:
        account = Account.from_key(req.private_key)
        
        if not web3.is_address(req.to_address):
            raise Exception("Invalid Address")
        
        # Initialize USDT contract
        usdt_contract = web3.eth.contract(address=USDT_CONTRACT_ADDRESS, abi=USDT_ABI)
        
        # Convert amount to USDT units (USDT has 6 decimals)
        amount = int(req.amount * 10**6)
        
        # Check if the balance is sufficient
        balance = usdt_contract.functions.balanceOf(account.address).call()
        if balance < amount:
            raise Exception("Insufficient balance")
        if account.address != req.from_address:
            raise Exception("Incorrect address")
        # Build transaction
        txn = usdt_contract.functions.transfer(
            req.to_address,
            amount
        ).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 100000,  # Adjust gas limit as needed
            'gasPrice': web3.eth.gas_price
        })
        
        # Sign and send
        signed_txn = web3.eth.account.sign_transaction(txn, req.private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Fixed: raw_transaction (not rawTransaction)
        
        return tx_hash.hex()
    except Exception as ex:
        raise RuntimeError(f"USDT transfer failed: {ex}")

def send_usdt_bep20(req:SendTransactionDTO):
    try:
        # Connect to BSC node
        rpc_url = "https://bsc-dataseed.binance.org/"
        web3 = Web3(Web3.HTTPProvider(rpc_url))

        if not web3.is_connected():
            raise Exception("Failed to connect to Binance Smart Chain node.")

        # Sender address from the private key
        sender_address = web3.eth.account.from_key(req.private_key).address

        if sender_address is not req.from_address:
            raise Exception("Invalid address")

        # USDT Contract ABI (minimal for transfer function)
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
            }
        ]

        # USDT Contract address
        usdt_contract_address = "0x55d398326f99059fF775485246999027B3197955"
        token_contract = web3.eth.contract(address=Web3.to_checksum_address(usdt_contract_address), abi=abi)

        # Calculate the amount in smallest unit (Wei)
        amount_in_wei = int(req.amount * 1e18)

        # Build the transaction
        nonce = web3.eth.get_transaction_count(sender_address)
        gas_price = web3.eth.gas_price
        gas_limit = 100000  # Adjust based on the complexity of the transaction

        transaction = token_contract.functions.transfer(
            Web3.to_checksum_address(req.to_address),
            amount_in_wei
        ).build_transaction({
            'chainId': 56,  # BSC Mainnet Chain ID
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': nonce
        })

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(transaction, req.private_key)

        # Broadcast the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return web3.to_hex(tx_hash)
    except Exception as ex:
        raise RuntimeError(f"USDT transfer failed: {ex}")