import requests
from django.conf import settings
from web3 import Web3
from xrpl.clients import JsonRpcClient
from xrpl.account import get_balance
from tronpy import Tron

# Get wallet balance of each coin

# BTC

def get_btc_balance_and_history(address):
    api_url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/full"
    response = requests.get(api_url)
    data = response.json()
    balance = data.get("final_balance", 0) / 1e8  # Convert satoshis to BTC
    return balance

def get_eth_balance_and_history(address):
    infura_url = 'https://mainnet.infura.io/v3/'+settings.INFURA
    # infura_url = 'HTTP://127.0.0.1:7545'
    web3 = Web3(Web3.HTTPProvider(infura_url))
    balance = web3.eth.get_balance(address)
    return int(balance) / 1e18

def get_sol_balance_and_history(address):
    # Get balance
    payload_balance = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    balance_response = requests.post("https://api.mainnet-beta.solana.com", json=payload_balance)
    print(balance_response.json())
    balance = balance_response.json()["result"]["value"] / 1e9  # Convert lamports to SOL
    return balance


def get_xrp_balance_and_history(address):
    client = JsonRpcClient("https://s2.ripple.com:51234/")

    # Get balance
    balance = get_balance(address, client)

    # Get transactions
    # transactions = get_account_transactions(address, client)

    return balance

def get_bnb_balance_and_history(address):
    # Get balance
    balance_url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&apikey={settings.BNB_API_KEY}"
    balance_response = requests.get(balance_url)
    balance_wei = int(balance_response.json().get("result", 0))
    balance_bnb = balance_wei / 1e18  # Convert from Wei to BNB
    return balance_bnb

def get_dodge_balance(address):
  response = requests.get(f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/full")
  data = response.json()
  balance = data.get("final_balance", 0) / 1e8  # Convert satoshis to BTC
  return balance

def get_tron_balance(address):
  client = Tron()

  balance = client.get_account_balance(address)
  return balance

# def get_usdt_balance(address):
#     url = f"https://api.bscscan.com/api?module=account&action=balance&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&address={address}&apikey={settings.BNB_API_KEY}"
#     response = requests.get(url)
#     return int(response.json()["result"]) / 1e6  # Assuming 6 decimals for USDT
def get_usdt_balance(address):
    # Connect to BSC node
    infura_url = 'https://mainnet.infura.io/v3/'+settings.INFURA
    web3 = Web3(Web3.HTTPProvider(infura_url))

    # USDT Contract ABI (only minimal ABI for balanceOf)
    abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]

    # Contract instance
    token_contract = web3.eth.contract(address=Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"), abi=abi)

    # Get balance
    balance = token_contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
    return web3.from_wei(balance, 'ether')  # Convert Wei to USDT