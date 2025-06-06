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
    try:
        balance_url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&apikey={settings.BNB_API_KEY}"
        balance_response = requests.get(balance_url)
        response_data = balance_response.json()

        # Check API response status
        if response_data.get('status') != '1':
            print(f"BSCScan API Error: {response_data.get('message', 'Unknown error')}")
            return 0

        # Safely parse balance
        balance_wei = int(response_data.get('result', 0))
        balance_bnb = balance_wei / 1e18  # Convert from Wei to BNB
        return balance_bnb

    except (ValueError, TypeError, KeyError) as e:
        print(f"Balance retrieval error: {e}")
        return 0

def get_dodge_balance(address):
  response = requests.get(f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/full")
  data = response.json()
  balance = data.get("final_balance", 0) / 1e8  # Convert satoshis to BTC
  return balance

def get_wdodge_balance(address):
    """
    Get WDODGE (Wrapped Dogecoin) balance for an address
    WDODGE is an ERC-20 token on Ethereum (and potentially other EVM chains)
    """
    try:
        # Initialize Web3
        infura_url = 'https://mainnet.infura.io/v3/'+settings.INFURA
        web3 = Web3(Web3.HTTPProvider(infura_url))
        
        # WDODGE contract address (mainnet example - verify actual address)
        WDODGE_CONTRACT = Web3.to_checksum_address("0x7B4328c127B85369D9f82ca0503B000D09CF9180")
        
        # ERC-20 ABI (simplified for balance check)
        ERC20_ABI = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Create contract instance
        contract = web3.eth.contract(address=WDODGE_CONTRACT, abi=ERC20_ABI)
        
        # Get balance (in smallest units)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
        
        # Convert to standard units (WDODGE uses 8 decimals like DOGE)
        return balance / 10**8
        
    except Exception as e:
        print(f"Error fetching WDODGE balance: {e}")
        return 0

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
    rpc_url = 'https://bsc-dataseed.binance.org/'  # Binance Smart Chain mainnet
    web3 = Web3(Web3.HTTPProvider(rpc_url))

    # Ensure the address is checksummed
    checksum_address = Web3.to_checksum_address(address)

    # USDT BEP20 Contract address (BSC)
    usdt_bep20_contract = "0x55d398326f99059fF775485246999027B3197955"

    # Minimal ABI for balanceOf
    abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]

    # Create contract instance
    token_contract = web3.eth.contract(address=Web3.to_checksum_address(usdt_bep20_contract), abi=abi)

    # Call balanceOf function
    raw_balance = token_contract.functions.balanceOf(checksum_address).call()

    # Convert using correct decimal for USDT (6)
    readable_balance = raw_balance / (10 ** 18)
    return readable_balance