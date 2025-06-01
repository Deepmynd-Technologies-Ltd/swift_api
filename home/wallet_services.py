from typing import Dict, List, Optional, Callable, Union
import requests
from decimal import Decimal
from enum import Enum
import time
from web3 import Web3
from http import HTTPStatus
from django.conf import settings
from home.wallet_schema import (
    Symbols, SendTransactionDTO, WalletResponseDTO, HTTPStatusCode,
    TransactionsInfo, WalletInfoResponse, BuySellProvider
)
from helper.generate_wallet import generate_mnemonic, generate_wallets_from_seed
import json
from helper.send_transaction.send_sol import send_sol
from helper.send_transaction.send_bnb import send_bnb
from helper.send_transaction.send_btc import send_btc
from helper.send_transaction.send_eth import send_eth
from helper.send_transaction.send_usdt import send_usdt
from helper.send_transaction.send_tron import send_trx
from helper.send_transaction.send_doge import send_doge

from helper.wallet_balance import (
    get_bnb_balance_and_history, get_btc_balance_and_history,
    get_dodge_balance, get_eth_balance_and_history,
    get_sol_balance_and_history, get_tron_balance, get_usdt_balance
)
from helper.wallet_transaction import (
    get_bnb_transactions, get_btc_transactions,
    get_dodge_transactions, get_eth_transactions,
    get_sol_transactions, get_trx_transactions, get_usdt_transactions
)

class FiatCurrency(str, Enum):
    USD = "USD"
    NGN = "NGN"
    EUR = "EUR"
    GBP = "GBP"

class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"

# Mapping between string symbols and Symbols enum
SYMBOL_MAP = {
    'BNB': Symbols.BNB,
    'BTC': Symbols.BTC,
    'ETH': Symbols.ETH,
    'SOL': Symbols.SOL,
    'TRON': Symbols.TRON,
    'USDT': Symbols.USDT,
    'DODGE': Symbols.DODGE,
    'USD': FiatCurrency.USD,
    'NGN': FiatCurrency.NGN,
    'EUR': FiatCurrency.EUR,
    'GBP': FiatCurrency.GBP
}

SYMBOL_TO_CHAIN_ID = {
    "eth": 1,
    "bnb": 56,
    "matic": 137,
    "btc": 20000000000001,
    "dodge": 1,
    "sol": 1151111081099710,
    "usdt": 1,
}

TOKEN_CONFIG = {
    Symbols.BNB: {
        "chain": "bsc", 
        "chain_id": 56, 
        "native": True, 
        "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "decimals": 18
    },
    Symbols.BTC: {
        "chain": "bitcoin", 
        "chain_id": 20000000000001, 
        "native": True, 
        "address": "bitcoin",
        "decimals": 8
    },
    Symbols.DODGE: {
        "chain": "dogechain", 
        "chain_id": 56, 
        "native": True, 
        "address": "0xbA2aE424d960c26247Dd6c32edC70B295c744C43",
        "decimals": 8
    },
    Symbols.ETH: {
        "chain": "ethereum", 
        "chain_id": 1, 
        "native": True, 
        "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "decimals": 18
    },
    Symbols.SOL: {
        "chain": "solana", 
        "chain_id": 1151111081099710, 
        "native": True, 
        "address": "So11111111111111111111111111111111111111112",
        "decimals": 9
    },
    Symbols.USDT: {
        "chain": "ethereum", 
        "chain_id": 1, 
        "native": False, 
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6
    },
}

# Monetization configuration for swaps
SWAP_MONETIZATION = {
    'fee_percent': Decimal('0.005'),  # 0.5% fee
    'min_fee_usd': Decimal('1.00'),  # $1 minimum fee
    'fee_recipient': settings.SWAP_FEE_RECIPIENT if hasattr(settings, 'SWAP_FEE_RECIPIENT') else '0x4e94F8Dfc57dF2f1433e3679f6Bcb427aF73f1ce',
    'integrator': 'your_company_id',
    'fee_tiers': {
        'high_volume': {'threshold': Decimal('10000'), 'fee': Decimal('0.003')},
        'medium_volume': {'threshold': Decimal('1000'), 'fee': Decimal('0.004')},
        'default': {'fee': Decimal('0.005')}
    }
}

def calculate_swap_fee(amount: Decimal, from_symbol: str, to_symbol: str) -> Dict:
    """Calculate swap fees based on monetization strategy."""
    try:
        # Ensure amount is Decimal
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        # Get current price for fee calculation in USD
        usd_price = get_token_usd_price(from_symbol)
        amount_usd = amount * usd_price
        
        # Determine fee tier
        fee_tier = SWAP_MONETIZATION['fee_tiers']['default']
        for tier_name, tier in SWAP_MONETIZATION['fee_tiers'].items():
            if tier_name != 'default' and amount_usd >= Decimal(str(tier['threshold'])):
                fee_tier = tier
                break
        
        fee_percent = Decimal(str(fee_tier['fee']))
        fee_amount = amount * fee_percent
        
        # Convert to minimum fee in token terms
        min_fee_token = Decimal(str(SWAP_MONETIZATION['min_fee_usd'])) / usd_price
        final_fee = max(fee_amount, min_fee_token)
        
        return {
            'gross_amount': amount,
            'net_amount': amount - final_fee,
            'fee_amount': final_fee,
            'fee_percent': fee_percent,
            'fee_currency': from_symbol,
            'fee_recipient': SWAP_MONETIZATION['fee_recipient']
        }
    except Exception as e:
        raise ValueError(f"Failed to calculate swap fee: {str(e)}")

def get_token_usd_price(symbol: str) -> Decimal:
    """Get current token price in USD (simplified - implement actual price feed)"""
    # In a real implementation, you'd query a price oracle or API
    prices = {
        'BTC': Decimal('40000'),
        'ETH': Decimal('3000'),
        'BNB': Decimal('400'),
        'SOL': Decimal('100'),
        'USDT': Decimal('1'),
        'DODGE': Decimal('0.1')
    }
    return prices.get(symbol.upper(), Decimal('1'))

def convert_to_symbol(symbol: Union[Symbols, str]) -> Symbols:
    """Convert a string symbol to Symbols enum."""
    if isinstance(symbol, Symbols):
        return symbol
    try:
        return SYMBOL_MAP[symbol.upper()]
    except KeyError:
        raise ValueError(f"Invalid symbol: {symbol}")

def handle_wallet_response(func: Callable, *args, **kwargs) -> WalletResponseDTO:
    """Generic handler for wallet operations."""
    try:
        data = func(*args, **kwargs)
        return WalletResponseDTO(data=data, message=f"{func.__name__} successful")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def get_token_config(symbol: Union[Symbols, str]) -> Dict:
    """Get token configuration with fallback to BSC for USDT."""
    try:
        symbol = convert_to_symbol(symbol)
    except ValueError as e:
        return None
    
    config = TOKEN_CONFIG.get(symbol)
    return config.get("bsc") if isinstance(config, dict) and "chain" not in config else config

# Wallet Core Functions (unchanged)
generate_secrete_phrases = lambda: handle_wallet_response(generate_mnemonic)
import_from_phrases = lambda phrase: handle_wallet_response(generate_wallets_from_seed, phrase)

def get_wallet_balance(symbol: Union[Symbols, str], address: str) -> WalletResponseDTO[float]:
    try:
        symbol = convert_to_symbol(symbol)
    except ValueError as e:
        return WalletResponseDTO(
            message=str(e),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )
    
    handlers = {
        Symbols.BTC: get_btc_balance_and_history,
        Symbols.ETH: get_eth_balance_and_history,
        Symbols.SOL: get_sol_balance_and_history,
        Symbols.DODGE: get_dodge_balance,
        Symbols.BNB: get_bnb_balance_and_history,
        Symbols.TRON: get_tron_balance,
        Symbols.USDT: get_usdt_balance,
    }
    return handle_wallet_response(handlers.get(symbol), address=address)

def get_all_transactions_history(symbol: Union[Symbols, str], address: str) -> WalletResponseDTO[List[TransactionsInfo]]:
    try:
        symbol = convert_to_symbol(symbol)
    except ValueError as e:
        return WalletResponseDTO(
            message=str(e),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )
    
    handlers = {
        Symbols.BTC: get_btc_transactions,
        Symbols.ETH: get_eth_transactions,
        Symbols.SOL: get_sol_transactions,
        Symbols.DODGE: get_dodge_transactions,
        Symbols.BNB: get_bnb_transactions,
        Symbols.TRON: get_trx_transactions,
        Symbols.USDT: get_usdt_transactions,
    }
    return handle_wallet_response(handlers.get(symbol), address)

def send_crypto_transaction(symbol: Union[Symbols, str], req: SendTransactionDTO) -> WalletResponseDTO[str]:
    try:
        symbol = convert_to_symbol(symbol)
    except ValueError as e:
        return WalletResponseDTO(
            message=str(e),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )
    
    handlers = {
        Symbols.BTC: lambda: send_btc(req, symbol),
        Symbols.ETH: lambda: send_eth(req),
        Symbols.SOL: lambda: send_sol(req),
        Symbols.DODGE: lambda: send_doge(req, symbol),
        Symbols.BNB: lambda: send_bnb(req),
        Symbols.TRON: lambda: send_tron(req),
        Symbols.USDT: lambda: send_usdt(req),
    }
    return handle_wallet_response(handlers.get(symbol))

def get_swap_quote(from_symbol: str, to_symbol: str, amount: Union[str, float, Decimal], 
                  from_address: str, to_address: Optional[str] = None, order: str = "RECOMMENDED", slippage: float = 0.5) -> Dict:
    """Get a quote for swapping tokens using LiFi, with monetization applied."""
    try:
        # Convert amount to Decimal if it's not already
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        from_config = get_token_config(from_symbol)
        to_config = get_token_config(to_symbol)
        
        if not from_config or not to_config:
            return {"success": False, "message": "Invalid token symbols"}

        # Calculate monetization fee
        fee_details = calculate_swap_fee(amount, from_symbol, to_symbol)
        effective_amount = fee_details['net_amount']

        # Convert amount to wei
        decimals = from_config.get("decimals", 18)
        amount_wei = int(effective_amount * (Decimal(10) ** decimals))

        params = {
            "fromChain": from_config.get("chain_id"),
            "toChain": to_config.get("chain_id"),
            "fromToken": from_config.get("address"),
            "toToken": to_config.get("address"),
            "fromAddress": from_address,
            "fromAmount": str(amount_wei),
            "slippage": Decimal(str(slippage)) / Decimal(100),
            "integrator": SWAP_MONETIZATION['integrator'],
            "fee": float(fee_details['fee_percent'] * 100),  # Convert to basis points
            "feeRecipient": SWAP_MONETIZATION['fee_recipient']
        }

        if to_address:
            params["toAddress"] = to_address

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
            headers["x-lifi-api-key"] = settings.LIFI_API_KEY

        response = requests.get("https://li.quest/v1/quote", headers=headers, params=params)
        if response.status_code == 200:
            quote_data = response.json()
            # Add fee details to the response
            quote_data['fee_details'] = fee_details
            return {"success": True, "data": quote_data}
        return {"success": False, "message": f"LiFi API error: {response.text}"}
    except Exception as ex:
        return {"success": False, "message": str(ex)}


def prepare_swap(from_symbol: str, to_symbol: str, amount: Union[str, float, Decimal], 
                from_address: str, to_address: Optional[str] = None, slippage: float = 0.5) -> Dict:
    """Prepare swap transaction data."""
    quote_result = get_swap_quote(from_symbol, to_symbol, amount, from_address, to_address, slippage)
    
    if not quote_result.get("success"):
        return quote_result

    quote_data = quote_result.get("data", {})
    
    step_data = {
        "id": quote_data.get("id"),
        "type": "lifi",
        "tool": quote_data.get("tool"),
        "toolDetails": quote_data.get("toolDetails", {}),
        "action": quote_data.get("action", {}),
        "estimate": quote_data.get("estimate", {}),
        "integrator": "lifi-api",
        "fromAddress": from_address,
        "slippage": slippage / 100,
        "includedSteps": quote_data.get("includedSteps", [])
    }
    
    if to_address:
        step_data["toAddress"] = to_address

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
        headers["x-lifi-api-key"] = settings.LIFI_API_KEY

    try:
        response = requests.post("https://li.quest/v1/advanced/stepTransaction", 
                               headers=headers, json=step_data)
        
        if response.status_code != 200:
            return {"success": False, "message": f"LiFi API error: {response.text}"}

        transaction_data = response.json()
        
        result = {
            **{k: v for k, v in quote_data.items() if k not in ['id']},
            "id": quote_data.get("id"),
            "transactionRequest": transaction_data.get("transactionRequest", {})
        }

        return {"success": True, "message": "Swap prepared successfully", "data": result}
        
    except Exception as ex:
        return {"success": False, "message": str(ex)}

def process_swap(from_symbol: str, to_symbol: str, amount: Union[str, float, Decimal],
                from_address: str, to_address: Optional[str] = None, slippage: float = 0.5,
                execute: bool = False, private_key: Optional[str] = None,
                web3_provider_url: Optional[str] = None, order: str = "RECOMMENDED", gas_multiplier: float = 1.1) -> Dict:
    """Process swap with optional execution."""
    
    # Get quote and prepare transaction
    prepare_result = prepare_swap(from_symbol, to_symbol, amount, from_address, to_address, slippage)
    
    if not prepare_result.get("success"):
        return prepare_result

    result_data = prepare_result.get("data", {})
    
    # Return early if not executing
    if not execute:
        return prepare_result
        
    if not private_key:
        return {"success": False, "message": "Private key required for execution"}
        
    # Determine chain type
    from_config = get_token_config(from_symbol)
    to_config = get_token_config(to_symbol)
    is_solana = (from_config.get("chain") == "solana" or to_config.get("chain") == "solana")
    
    transaction_request = result_data.get("transactionRequest", {})
    
    if is_solana:
        return _execute_solana_transaction(transaction_request, private_key, result_data)
    else:
        return _execute_evm_transaction(transaction_request, private_key, web3_provider_url, 
                                      gas_multiplier, result_data)

def _execute_solana_transaction(transaction_request: Dict, private_key: str, result_data: Dict) -> Dict:
    """Execute Solana transaction."""
    try:
        import base58
        from nacl.signing import SigningKey
        
        # Parse private key
        if private_key.startswith('[') and private_key.endswith(']'):
            key_bytes = bytes(eval(private_key))
        elif len(private_key) == 64:
            key_bytes = bytes.fromhex(private_key)
        else:
            key_bytes = base58.b58decode(private_key)
            
        if len(key_bytes) > 32:
            key_bytes = key_bytes[:32]
            
        signing_key = SigningKey(key_bytes)
        
        # Get transaction data
        serialized_tx = transaction_request.get('data') or transaction_request.get('transaction')
        if not serialized_tx:
            return {"success": False, "message": "No transaction data found"}
        
        # Send transaction
        rpc_url = "https://api.mainnet-beta.solana.com"
        send_request = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "sendTransaction",
            "params": [serialized_tx, {"skipPreflight": False, "encoding": "base64"}]
        }
        
        response = requests.post(rpc_url, json=send_request, timeout=30)
        
        if response.status_code != 200:
            return {"success": False, "message": f"RPC request failed: {response.status_code}"}
        
        response_data = response.json()
        
        if 'error' in response_data:
            return {"success": False, "message": f"Solana RPC error: {response_data['error']['message']}"}
        
        tx_signature = response_data.get('result')
        
        return {
            "success": True,
            "message": "Solana swap executed successfully",
            "data": {
                "preparation": result_data,
                "execution": {
                    "transactionHash": tx_signature,
                    "fromAddress": base58.b58encode(signing_key.verify_key.encode()).decode('utf-8'),
                    "chain": "solana"
                }
            }
        }
        
    except Exception as ex:
        return {"success": False, "message": f"Solana execution failed: {str(ex)}"}

def _execute_evm_transaction(transaction_request: Dict, private_key: str, web3_provider_url: str,
                           gas_multiplier: float, result_data: Dict) -> Dict:
    """Execute EVM transaction."""
    try:
        if not web3_provider_url:
            return {"success": False, "message": "Web3 provider URL required"}
            
        w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        if not w3.is_connected():
            return {"success": False, "message": "Failed to connect to Web3 provider"}

        account = w3.eth.account.from_key(private_key)
        
        tx_params = {
            'chainId': transaction_request['chainId'],
            'to': Web3.to_checksum_address(transaction_request['to']),
            'value': int(transaction_request['value'], 16) if isinstance(transaction_request['value'], str) else transaction_request['value'],
            'data': transaction_request['data'],
            'from': account.address,
            'gasPrice': int(transaction_request['gasPrice'], 16) if isinstance(transaction_request['gasPrice'], str) else transaction_request['gasPrice'],
            'nonce': w3.eth.get_transaction_count(account.address),
        }

        # Estimate gas
        estimated_gas = w3.eth.estimate_gas(tx_params)
        tx_params['gas'] = int(estimated_gas * gas_multiplier)

        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return {
            "success": True,
            "message": "EVM swap executed successfully",
            "data": {
                "preparation": result_data,
                "execution": {
                    "transactionHash": tx_hash.hex(),
                    "fromAddress": account.address,
                    "chainId": tx_params['chainId'],
                    "chain": "evm"
                }
            }
        }
        
    except Exception as ex:
        return {"success": False, "message": f"EVM execution failed: {str(ex)}"}

def get_swap_status(tx_hash: str) -> Dict:
    """Get swap transaction status."""
    if not tx_hash:
        return {"success": False, "message": "Transaction hash required"}

    headers = {"Accept": "application/json"}
    if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
        headers["x-lifi-api-key"] = settings.LIFI_API_KEY

    try:
        response = requests.get("https://li.quest/v1/status", 
                              headers=headers, params={"txHash": tx_hash})
        
        if response.status_code == 200:
            data = response.json()
            data["provider"] = "lifi"
            return {"success": True, "data": data}
        return {"success": False, "message": f"Status API error: {response.text}"}
        
    except Exception as e:
        return {"success": False, "message": str(e)}