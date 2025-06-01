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

# Simplified Li.Fi Integration
def api_request_handler(url: str, method: str = "get", headers: Dict = None, 
                       payload: Dict = None, params: Dict = None) -> Dict:
    """Generic API request handler."""
    try:
        response = requests.request(method, url, headers=headers, json=payload, params=params)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False, "message": f"API error: {response.text}", "status_code": response.status_code}
    except Exception as ex:
        return {"success": False, "message": f"Exception: {str(ex)}", "status_code": 500}

def validate_token_amount(amount: Union[str, float, Decimal], symbol: str) -> Dict:
    """Validate that an amount is properly formatted for the token's decimals."""
    try:
        config = get_token_config(symbol)
        if not config:
            return {"valid": False, "message": f"Invalid token symbol: {symbol}"}
            
        decimals = config.get("decimals", 18)
        max_value = Decimal(10**decimals) - 1
        
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, float):
            amount = Decimal(str(amount))
            
        if amount <= 0:
            return {"valid": False, "message": "Amount must be positive"}
            
        if amount > max_value:
            return {"valid": False, "message": f"Amount exceeds maximum value for {symbol}"}
            
        return {"valid": True, "decimals": decimals, "amount_wei": int(amount * Decimal(10**decimals))}
        
    except Exception as e:
        return {"valid": False, "message": f"Validation error: {str(e)}"}

def get_swap_quote(
    from_symbol: str,
    to_symbol: str,
    amount: Decimal,
    from_address: str,
    to_address: Optional[str] = None,
    slippage: float = 0.5,
    order: str = "RECOMMENDED"
) -> Dict:
    """Get a quote for swapping tokens using LiFi."""
    try:
        # Get token configurations
        from_config = get_token_config(from_symbol)
        to_config = get_token_config(to_symbol)
        
        if not from_config or not to_config:
            return {
                "success": False,
                "message": "Invalid token symbols provided",
                "status_code": HTTPStatusCode.BAD_REQUEST
            }

        # Get token addresses
        from_token = from_config.get("address")
        to_token = to_config.get("address")
        
        try:
            if isinstance(amount, str):
                amount = Decimal(amount)
            
            # Get the correct decimal places
            decimals = from_config.get("decimals", 18)  # Default to 18 if not specified
            
            # Convert amount to smallest units (wei/satoshi/etc.)
            amount_wei = int(amount * Decimal(10**decimals))
                
        except Exception as conv_ex:
            return {
                "success": False,
                "message": f"Invalid amount format: {str(conv_ex)}. Example valid amount: '1.5' for 1.5 {from_symbol}",
                "status_code": HTTPStatusCode.BAD_REQUEST
            }
        
        params = {
            "fromChain": from_config.get("chain_id"),
            "toChain": to_config.get("chain_id"),
            "fromToken": from_token,
            "toToken": to_token,
            "fromAddress": from_address,
            "fromAmount": str(amount_wei),
            "slippage": slippage / 100,
            "order": order
        }
        
        if to_address:
            params["toAddress"] = to_address
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add API key if configured
        if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
            headers["x-lifi-api-key"] = settings.LIFI_API_KEY
        
        # Make the API request with detailed error handling
        result = api_request_handler("https://li.quest/v1/quote", "get", headers=headers, params=params)
        
        if not result.get("success"):
            # If the API returned an error, use its message
            error_msg = result.get("message", "Unknown API error")
            if "data" in result and isinstance(result["data"], dict):
                error_msg = result["data"].get("message", error_msg)
            return {
                "success": False,
                "message": f"LiFi API error: {error_msg}",
                "status_code": result.get("status_code", HTTPStatusCode.BAD_REQUEST),
                "data": result.get("data")
            }
        return {
            "success": True,
            "quote_id": result.get("quoteId"),
            "message": "Swap quote retrieved successfully",
            "status_code": HTTPStatusCode.OK,
            "data": result.get("data")
        }
        
    except Exception as ex:
        # Get the most detailed error message possible
        error_msg = str(ex) or "Unknown error"
        if hasattr(ex, '__dict__'):
            error_msg = getattr(ex, 'message', error_msg)
            error_msg = getattr(ex, 'args', [error_msg])[0]
        
        return {
            "success": False,
            "message": f"Failed to get swap quote: {error_msg}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "exception_type": ex.__class__.__name__ if hasattr(ex, '__class__') else None
        }

def prepare_swap(
    from_symbol: Union[str, int],
    to_symbol: Union[str, int],
    amount: Union[str, float, Decimal],
    from_address: str,
    to_address: Optional[str] = None,
    slippage: float = 0.5,
    order: str = "RECOMMENDED"
) -> Dict:
    """
    Unified function to handle the entire swap process:
    1. Get a swap quote
    2. Prepare the transaction data
    3. Return the transaction data ready for signing
    """
    try:
        # Get token configurations
        from_config = get_token_config(from_symbol)
        to_config = get_token_config(to_symbol)
        
        if not from_config or not to_config:
            return {
                "success": False,
                "message": "Invalid token symbols provided",
                "status_code": HTTPStatusCode.BAD_REQUEST
            }

        # Step 1: Get the swap quote
        quote_result = get_swap_quote(
            from_symbol=from_symbol,
            to_symbol=to_symbol,
            amount=amount,
            from_address=from_address,
            to_address=to_address,
            slippage=slippage,
            order=order
        )
        
        if not quote_result.get("success"):
            return quote_result

        quote_data = quote_result.get("data", {})
        
        # Prepare the step payload with all required fields
        step_data = {
            "id": quote_data.get("id"),
            "type": "lifi",  # Set type to 'lifi'
            "tool": quote_data.get("tool"),
            "toolDetails": quote_data.get("toolDetails", {}),
            "action": quote_data.get("action", {}),
            "estimate": quote_data.get("estimate", {}),
            "integrator": quote_data.get("integrator", "lifi-api"),
            "fromAddress": from_address,
            "slippage": slippage / 100,
            "includedSteps": quote_data.get("includedSteps", [])  # Add includedSteps from quote
        }
        
        # Add toAddress if provided
        if to_address:
            step_data["toAddress"] = to_address

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
            headers["x-lifi-api-key"] = settings.LIFI_API_KEY

        # Make the API request to get transaction data
        response = requests.post(
            "https://li.quest/v1/advanced/stepTransaction",
            headers=headers,
            json=step_data
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": f"LiFi API error: {response.text}",
                "status_code": response.status_code,
                "data": response.json() if response.content else {}
            }

        transaction_data = response.json()
        
        # Combine all the data into the desired format
        result = {
            "type": quote_data.get("type", "lifi"),
            "toolDetails": quote_data.get("toolDetails", {}),
            "action": quote_data.get("action", {}),
            "estimate": quote_data.get("estimate", {}),
            "id": quote_data.get("id"),
            "tool": quote_data.get("tool"),
            "integrator": quote_data.get("integrator", "lifi-api"),
            "includedSteps": quote_data.get("includedSteps", []),
            "transactionRequest": transaction_data.get("transactionRequest", {})
        }

        return {
            "success": True,
            "message": "Swap execution prepared successfully",
            "status_code": HTTPStatusCode.OK,
            "data": result
        }

    except Exception as ex:
        error_msg = str(ex) or "Unknown error occurred during swap execution"
        return {
            "success": False,
            "message": f"Failed to execute swap: {error_msg}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "exception_type": ex.__class__.__name__
        }

def process_swap(
    from_symbol: Union[str, int],
    to_symbol: Union[str, int],
    amount: Union[str, float, Decimal],
    from_address: str,
    to_address: Optional[str] = None,
    slippage: float = 0.5,
    order: str = "RECOMMENDED",
    execute: bool = False,
    private_key: Optional[str] = None,
    web3_provider_url: Optional[str] = None,
    gas_multiplier: float = 1.1
) -> Dict:
    """Unified function to handle swap process for both EVM chains and Solana."""
    quote_data = None
    amount_validation = validate_token_amount(amount, from_symbol)
    
    if not amount_validation.get("valid"):
        return {
            "success": False,
            "message": amount_validation.get("message"),
            "status_code": HTTPStatusCode.BAD_REQUEST
        }
    
    try:
        # Get token configurations
        from_config = get_token_config(from_symbol)
        to_config = get_token_config(to_symbol)
        
        if not from_config or not to_config:
            return {
                "success": False,
                "message": "Invalid token symbols provided",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": None,
                "quote_data": None
            }

        # Determine if this involves Solana
        is_solana_transaction = (
            from_config.get("chain") == "solana" or 
            to_config.get("chain") == "solana"
        )

        # Step 1: Get the swap quote and prepare transaction
        prepare_result = get_swap_quote(
            from_symbol=from_symbol,
            to_symbol=to_symbol,
            amount=amount,
            from_address=from_address,
            to_address=to_address,
            slippage=slippage,
            order=order
        )
        
        if not prepare_result.get("success"):
            return {
                "success": False,
                "message": prepare_result.get("message"),
                "status_code": prepare_result.get("status_code", HTTPStatusCode.BAD_REQUEST),
                "data": None,
                "quote_data": None
            }

        quote_data = prepare_result.get("data", {})
        
        # Prepare the step payload with all required fields
        step_data = {
            "id": quote_data.get("id"),
            "type": "lifi",
            "tool": quote_data.get("tool"),
            "toolDetails": quote_data.get("toolDetails", {}),
            "action": quote_data.get("action", {}),
            "estimate": quote_data.get("estimate", {}),
            "integrator": quote_data.get("integrator", "lifi-api"),
            "fromAddress": from_address,
            "slippage": slippage / 100,
            "includedSteps": quote_data.get("includedSteps", [])
        }
        
        if to_address:
            step_data["toAddress"] = to_address

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
            headers["x-lifi-api-key"] = settings.LIFI_API_KEY

        # Get transaction data from LiFi
        response = requests.post(
            "https://li.quest/v1/advanced/stepTransaction",
            headers=headers,
            json=step_data
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": f"LiFi API error: {response.text}",
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "quote_data": quote_data
            }

        transaction_data = response.json()
        
        # Prepare the response data structure
        result = {
            "type": quote_data.get("type", "lifi"),
            "toolDetails": quote_data.get("toolDetails", {}),
            "action": quote_data.get("action", {}),
            "estimate": quote_data.get("estimate", {}),
            "id": quote_data.get("id"),
            "tool": quote_data.get("tool"),
            "integrator": quote_data.get("integrator", "lifi-api"),
            "includedSteps": quote_data.get("includedSteps", []),
            "transactionRequest": transaction_data.get("transactionRequest", {}),
            "chain_type": "solana" if is_solana_transaction else "evm"
        }

        # Return early if we're only preparing
        if not execute:
            return {
                "success": True,
                "message": "Swap prepared successfully",
                "status_code": HTTPStatusCode.OK,
                "data": result,
                "quote_data": quote_data
            }
            
        # Step 2: Execute the transaction if requested
        if not private_key:
            return {
                "success": False,
                "message": "Private key is required for execution",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": result,
                "quote_data": quote_data
            }
            
        transaction_request = transaction_data.get("transactionRequest", {})
        if not transaction_request:
            return {
                "success": False,
                "message": "Transaction request data is missing",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": result,
                "quote_data": quote_data
            }

        # Handle execution based on chain type
        if is_solana_transaction:
            return _execute_solana_transaction(
                transaction_request, private_key, result, quote_data
            )
        else:
            return _execute_evm_transaction(
                transaction_request, private_key, web3_provider_url, 
                gas_multiplier, result, quote_data
            )

    except Exception as ex:
        error_msg = str(ex) or "Unknown error occurred during swap process"
        return {
            "success": False,
            "message": f"Failed to process swap: {error_msg}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "data": None,
            "quote_data": quote_data
        }


def _execute_solana_transaction(
    transaction_request: Dict, 
    private_key: str, 
    result: Dict, 
    quote_data: Dict
) -> Dict:
    """Execute Solana transaction using HTTP requests to Solana RPC."""
    try:
        import requests
        import json
        import base64
        import base58
        from nacl.signing import SigningKey
        from nacl.encoding import Base64Encoder
        
        # Solana RPC endpoint
        rpc_url = "https://api.mainnet-beta.solana.com"
        
        # Validate RPC connection
        try:
            health_response = requests.post(
                rpc_url,
                json={"id": 1, "jsonrpc": "2.0", "method": "getHealth"},
                timeout=10
            )
            if health_response.status_code != 200:
                raise Exception("RPC not accessible")
        except Exception as health_error:
            return {
                "success": False,
                "message": f"Failed to connect to Solana RPC: {str(health_error)}",
                "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                "data": result,
                "quote_data": quote_data
            }

        # Parse private key
        try:
            print(f"Private key length: {len(private_key)}")
            print("Private key content", private_key)
            
            if private_key.startswith('[') and private_key.endswith(']'):
                # Array format
                key_bytes = bytes(eval(private_key))
            elif len(private_key) == 64:
                # Hex format (32 bytes = 64 hex characters)
                key_bytes = bytes.fromhex(private_key)
            elif len(private_key) == 128:
                # Longer hex format (64 bytes = 128 hex characters, need first 32)
                key_bytes = bytes.fromhex(private_key)[:32]
            else:
                # Base58 format
                try:
                    key_bytes = base58.b58decode(private_key)
                except Exception:
                    # If base58 decode fails, try hex decode as fallback
                    key_bytes = bytes.fromhex(private_key)
            
            # Ensure we have exactly 32 bytes for the private key
            if len(key_bytes) > 32:
                key_bytes = key_bytes[:32]
            elif len(key_bytes) < 32:
                raise Exception(f"Private key too short: {len(key_bytes)} bytes, need 32 bytes")
            
            # Create signing key
            signing_key = SigningKey(key_bytes)
            
        except Exception as key_error:
            return {
                "success": False,
                "message": f"Invalid private key format: {str(key_error)}",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": result,
                "quote_data": quote_data
            }

        # Extract and process transaction data
        try:
            # LiFi should provide a serialized transaction
            serialized_tx = None
            
            if 'data' in transaction_request:
                serialized_tx = transaction_request['data']
            elif 'transaction' in transaction_request:
                serialized_tx = transaction_request['transaction']
            else:
                return {
                    "success": False,
                    "message": "No serialized transaction data found in LiFi response",
                    "status_code": HTTPStatusCode.BAD_REQUEST,
                    "data": result,
                    "quote_data": quote_data
                }
            
            if not serialized_tx:
                return {
                    "success": False,
                    "message": "Empty transaction data from LiFi",
                    "status_code": HTTPStatusCode.BAD_REQUEST,
                    "data": result,
                    "quote_data": quote_data
                }
                
        except Exception as parse_error:
            return {
                "success": False,
                "message": f"Failed to parse transaction data: {str(parse_error)}",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": result,
                "quote_data": quote_data
            }

        # Send the pre-signed transaction from LiFi
        try:
            # If LiFi provides a pre-signed transaction, send it directly
            send_request = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "sendTransaction",
                "params": [
                    serialized_tx,
                    {
                        "skipPreflight": False,
                        "preflightCommitment": "processed",
                        "encoding": "base64",
                        "maxRetries": 3
                    }
                ]
            }
            
            response = requests.post(
                rpc_url,
                json=send_request,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"RPC request failed with status {response.status_code}",
                    "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                    "data": result,
                    "quote_data": quote_data
                }
            
            response_data = response.json()
            
            if 'error' in response_data:
                error_message = response_data['error'].get('message', 'Unknown RPC error')
                return {
                    "success": False,
                    "message": f"Solana RPC error: {error_message}",
                    "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                    "data": result,
                    "quote_data": quote_data,
                    "rpc_error": response_data['error']
                }
            
            tx_signature = response_data.get('result')
            if not tx_signature:
                return {
                    "success": False,
                    "message": "No transaction signature returned",
                    "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                    "data": result,
                    "quote_data": quote_data
                }
            
            # Optional: Check transaction status
            try:
                # Wait a moment for the transaction to be processed
                import time
                time.sleep(2)
                
                status_request = {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "getSignatureStatuses",
                    "params": [
                        [tx_signature],
                        {"searchTransactionHistory": True}
                    ]
                }
                
                status_response = requests.post(rpc_url, json=status_request, timeout=10)
                status_data = status_response.json()
                
                if 'result' in status_data and status_data['result']['value']:
                    status_info = status_data['result']['value'][0]
                    if status_info and status_info.get('err'):
                        return {
                            "success": False,
                            "message": f"Transaction failed on-chain: {status_info['err']}",
                            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                            "data": result,
                            "quote_data": quote_data,
                            "transaction_signature": tx_signature
                        }
                        
            except Exception as status_error:
                # Status check failed but transaction was sent
                pass
            
            return {
                "success": True,
                "message": "Solana swap transaction executed successfully",
                "status_code": HTTPStatusCode.OK,
                "data": {
                    "preparation": result,
                    "execution": {
                        "transactionHash": tx_signature,
                        "transactionSignature": tx_signature,
                        "fromAddress": base58.b58encode(signing_key.verify_key.encode()).decode('utf-8'),
                        "chain": "solana",
                        "status": "sent"
                    }
                },
                "quote_data": quote_data
            }
            
        except Exception as send_error:
            return {
                "success": False,
                "message": f"Failed to send Solana transaction: {str(send_error)}",
                "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                "data": result,
                "quote_data": quote_data
            }
            
    except Exception as ex:
        return {
            "success": False,
            "message": f"Solana transaction execution failed: {str(ex)}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "data": result,
            "quote_data": quote_data
        }


def _execute_evm_transaction(
    transaction_request: Dict, 
    private_key: str, 
    web3_provider_url: str, 
    gas_multiplier: float, 
    result: Dict, 
    quote_data: Dict
) -> Dict:
    """Execute EVM transaction using Web3."""
    try:
        if not web3_provider_url:
            return {
                "success": False,
                "message": "Web3 provider URL is required for EVM transactions",
                "status_code": HTTPStatusCode.BAD_REQUEST,
                "data": result,
                "quote_data": quote_data
            }
            
        # Initialize Web3 connection
        w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        if not w3.is_connected():
            return {
                "success": False,
                "message": "Failed to connect to Web3 provider",
                "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                "data": result,
                "quote_data": quote_data
            }

        # Get the account from private key
        account = w3.eth.account.from_key(private_key)
        
        # Prepare transaction parameters
        tx_params = {
            'chainId': transaction_request['chainId'],
            'to': Web3.to_checksum_address(transaction_request['to']),
            'value': int(transaction_request['value'], 16) if isinstance(transaction_request['value'], str) else transaction_request['value'],
            'data': transaction_request['data'],
            'from': account.address,
            'gasPrice': int(transaction_request['gasPrice'], 16) if isinstance(transaction_request['gasPrice'], str) else transaction_request['gasPrice'],
            'nonce': w3.eth.get_transaction_count(account.address),
        }

        # Estimate gas with a multiplier for safety
        try:
            estimated_gas = w3.eth.estimate_gas(tx_params)
            tx_params['gas'] = int(estimated_gas * gas_multiplier)
        except Exception as gas_error:
            return {
                "success": False,
                "message": f"Gas estimation failed: {str(gas_error)}",
                "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                "data": result,
                "quote_data": quote_data
            }

        # Sign and send the transaction
        try:
            signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
        except Exception as tx_error:
            return {
                "success": False,
                "message": f"Transaction failed: {str(tx_error)}",
                "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
                "data": result,
                "quote_data": quote_data
            }

        # Return successful execution result
        return {
            "success": True,
            "message": "EVM swap transaction executed successfully",
            "status_code": HTTPStatusCode.OK,
            "data": {
                "preparation": result,
                "execution": {
                    "transactionHash": tx_hash_hex,
                    "fromAddress": account.address,
                    "toAddress": tx_params['to'],
                    "chainId": tx_params['chainId'],
                    "value": str(tx_params['value']),
                    "gasPrice": str(tx_params['gasPrice']),
                    "gasLimit": str(tx_params['gas']),
                    "nonce": tx_params['nonce'],
                    "chain": "evm"
                }
            },
            "quote_data": quote_data
        }
        
    except Exception as ex:
        return {
            "success": False,
            "message": f"EVM transaction execution failed: {str(ex)}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "data": result,
            "quote_data": quote_data
        }

def get_swap_status(tx_hash: str) -> Dict:
    """Get the status of a swap transaction using LiFi API."""
    try:
        if not tx_hash:
            return {
                "success": False,
                "message": "Transaction hash is required",
                "status_code": HTTPStatusCode.BAD_REQUEST
            }

        headers = {
            "Accept": "application/json",
        }

        # Add API key if configured
        if hasattr(settings, 'LIFI_API_KEY') and settings.LIFI_API_KEY:
            headers["x-lifi-api-key"] = settings.LIFI_API_KEY

        params = {
            "txHash": tx_hash
        }

        # Make the API request
        result = api_request_handler(
            "https://li.quest/v1/status",
            method="get",
            headers=headers,
            params=params
        )

        if not result.get("success"):
            return {
                "success": False,
                "message": result.get("message", "Failed to get transaction status"),
                "status_code": result.get("status_code", HTTPStatusCode.BAD_REQUEST),
                "data": result.get("data")
            }

        # Add provider info
        if result.get("data"):
            result["data"]["provider"] = "lifi"
        
        return result

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get transaction status: {str(e)}",
            "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR,
            "exception_type": e.__class__.__name__
        }