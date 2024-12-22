from typing import List
import requests
from django.conf import settings

from home.wallet_schema import TransactionType, TransactionsInfo

def get_btc_transactions(address)->List[TransactionsInfo]:
  api_url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/full"
  response = requests.get(api_url)
  data = response.json()

  transactions:List[TransactionsInfo] = []
  for tx in data.get("txs", []):
      for output in tx.get("outputs", []):
            addresses = output.get("addresses")
            if addresses and address in addresses:  # Ensure addresses is not None
                val = TransactionsInfo(hash=tx["hash"], transaction_type=TransactionType.RECEIVED, amount=output["value"] / 1e8, timestamp=tx.get("confirmed", None))
                transactions.append(val)

      # Check inputs for sent transactions
      for input_tx in tx.get("inputs", []):
          addresses = input_tx.get("addresses")
          if addresses and address in addresses:  # Ensure addresses is not None
              val = TransactionsInfo(hash=tx["hash"], transaction_type=TransactionType.SENT, amount=input_tx["output_value"] / 1e8, timestamp=tx.get("confirmed", None))
              transactions.append(val)

  return transactions

def get_dodge_transactions(address)->List[TransactionsInfo]:
  api_url = f"https://api.blockcypher.com/v1/doge/main/addrs/{address}/full"
  response = requests.get(api_url)
  data = response.json()

  transactions:List[TransactionsInfo] = []
  for tx in data.get("txs", []):
      for output in tx.get("outputs", []):
            addresses = output.get("addresses")
            if addresses and address in addresses:  # Ensure addresses is not None
                val = TransactionsInfo(hash=tx["hash"], transaction_type=TransactionType.RECEIVED, amount=output["value"] / 1e8, timestamp=tx.get("confirmed", None))
                transactions.append(val)

      # Check inputs for sent transactions
      for input_tx in tx.get("inputs", []):
          addresses = input_tx.get("addresses")
          if addresses and address in addresses:  # Ensure addresses is not None
              val = TransactionsInfo(hash=tx["hash"], transaction_type=TransactionType.SENT, amount=input_tx["output_value"] / 1e8, timestamp=tx.get("confirmed", None))
              transactions.append(val)

  return transactions

def get_eth_transactions(address)->List[TransactionsInfo]:
    tx_url = f"https://api.etherscan.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,  # Fetch transactions from the beginning of the blockchain
        "endblock": 99999999,  # Until the latest block
        "sort": "desc",  # Sort transactions in descending order (latest first)
        "apikey": settings.ETH_API_KEY,
    }

    response = requests.get(tx_url, params=params)
    data = response.json()
    transactions:List[TransactionsInfo] = []

    transactions_data = data["result"][:10]  # Limit the number of transactions

    min_value_in_eth = 0.00001  # Minimum ETH threshold
    for tx in transactions_data:
        value_eth = int(tx["value"]) / 1e18
        if value_eth >= min_value_in_eth:
            tx_type = TransactionType.RECEIVED if tx["to"].lower() == address.lower() else TransactionType.SENT
            val = TransactionsInfo(hash=tx["hash"], transaction_type=tx_type, amount=value_eth, timestamp=tx["timeStamp"])
            transactions.append(val)

    return transactions

def parse_transaction(tx, address):
    """Parse individual transaction to determine type, amount, and timestamp."""
    tx_signature = tx["signature"]
    url = f"https://api.mainnet-beta.solana.com/"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [tx_signature, {"encoding": "jsonParsed"}]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch transaction details for {tx_signature}")
        return None

    tx_details = response.json().get("result")
    if not tx_details:
        print(f"No details found for transaction {tx_signature}")
        return None

    meta = tx_details.get("meta", {})
    message = tx_details.get("transaction", {}).get("message", {})
    account_keys = message.get("accountKeys", [])

    # Locate the wallet address index
    if address not in account_keys:
        print(f"Address {address} not found in accountKeys for transaction {tx_signature}")
        return None

    address_index = account_keys.index(address)
    pre_balances = meta.get("preBalances", [])
    post_balances = meta.get("postBalances", [])
    fee = meta.get("fee", 0)

    # Calculate balance change
    if len(pre_balances) > address_index and len(post_balances) > address_index:
        balance_change = post_balances[address_index] - pre_balances[address_index]

        # Determine type and amount
        if balance_change < 0:  # Sent transaction
            transaction_type = TransactionType.SENT
            amount = abs(balance_change) - fee  # Exclude fee from the amount
        else:  # Received transaction
            transaction_type = TransactionType.RECEIVED
            amount = balance_change
    else:
        return None
    return TransactionsInfo(hash=tx_signature, transaction_type=transaction_type, amount=amount / 10**9, timestamp=tx.get("blockTime"))


def get_sol_transactions(address)->List[TransactionsInfo]:
    """Fetch and parse transactions for a given Solana wallet address."""
    try:
        url = f"https://api.mainnet-beta.solana.com/"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": 10}]
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception("Failed to fetch transactions for address")

        tx_list = response.json().get("result", [])
        parsed_transactions:List[TransactionsInfo] = []

        for tx in tx_list:
            parsed_tx = parse_transaction(tx, address)
            if parsed_tx:
                parsed_transactions.append(parsed_tx)

        return parsed_transactions

    except Exception as e:
        print(f"An error occurred: {e}")
        raise Exception(str(e))

def get_trx_transactions(address)->List[TransactionsInfo]:
    base_url = "https://api.trongrid.io"
    tx_url = f"{base_url}/v1/accounts/{address}/transactions"
    response = requests.get(tx_url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch transactions: {response.text}")

    data = response.json().get("data", [])

    transactions:List[TransactionsInfo] = []
    for tx in data:
        # Safely check for required keys
        raw_data = tx.get("raw_data")
        if not raw_data:
            continue

        contract = raw_data.get("contract")

        parameter = contract[0].get("parameter", {}).get("value", {})
        to_address = parameter.get("to_address")
        from_address = parameter.get("owner_address")
        amount = parameter.get("amount", 0)

        if to_address and from_address:
            tx_type = TransactionType.RECEIVED if address in to_address else TransactionType.SENT
            val = TransactionsInfo(hash=tx.get("txID"), transaction_type=tx_type,amount=int(amount)/1e6, timestamp=tx.get("block_timestamp"))
            transactions.append(val)

    return transactions

def get_bnb_transactions(address)->List[TransactionsInfo]:
    # BscScan API endpoint for transaction history
    tx_url = f"https://api.bscscan.com/api?module=account&action=txlist&address={address}&sort=desc&apikey={settings.BNB_API_KEY}"
    response = requests.get(tx_url)
    transactions = response.json().get("result", [])

    formatted_transactions:List[TransactionsInfo] = []

    for tx in transactions:
        tx_type = TransactionType.SENT if tx["from"].lower() == address.lower() else TransactionType.RECEIVED
        val = TransactionsInfo(hash=tx["hash"], transaction_type=tx_type, amount=int(tx["value"]) / 1e18, timestamp=tx["timeStamp"])
        formatted_transactions.append(val)

    return formatted_transactions[:10]

def get_usdt_transactions(address)->List[TransactionsInfo]:
    url = f"https://api.bscscan.com/api?module=account&action=tokentx&contractaddress=0x55d398326f99059fF775485246999027B3197955&address={address}&apikey={settings.BNB_API_KEY}"
    response = requests.get(url)
    transactions = response.json().get("result", [])

    formatted_transactions:List[TransactionsInfo] = []
    for tx in transactions:
        tx_type = TransactionType.SENT if tx["from"].lower() == address.lower() else TransactionType.RECEIVED
        val = TransactionsInfo(hash=tx["hash"], transaction_type=tx_type, amount=int(tx["value"]) / 1e18, timestamp=tx["timeStamp"])
        formatted_transactions.append(val)
    return formatted_transactions