from typing import Dict, List, Optional, Callable, Union
import requests
from decimal import Decimal
from enum import Enum
import time
from django.conf import settings
from home.wallet_schema import (
    Symbols, SendTransactionDTO, WalletResponseDTO, HTTPStatusCode,
    TransactionsInfo, WalletInfoResponse, BuySellProvider
)
from helper.generate_wallet import generate_mnemonic, generate_wallets_from_seed
import json
from helper.send_transaction import (
    send_bnb, send_btc, send_eth, send_sol, send_usdt, send_tron
)
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

TOKEN_CONFIG = {
    Symbols.BNB: {"chain": "bsc", "chain_id": 56, "native": True, "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"},
    Symbols.BTC: {"chain": "bitcoin", "chain_id": "bitcoin", "native": True, "address": "native"},
    Symbols.DODGE: {"chain": "dogechain", "chain_id": "doge", "native": True, "address": "native"},
    Symbols.ETH: {"chain": "ethereum", "chain_id": 1, "native": True, "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"},
    Symbols.SOL: {"chain": "solana", "chain_id": "solana", "native": True, "address": "So11111111111111111111111111111111111111112"},
    Symbols.TRON: {"chain": "tron", "chain_id": "tron", "native": True, "address": "native"},
    Symbols.USDT: {
        "ethereum": {"chain": "ethereum", "chain_id": 1, "native": False, "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
        "bsc": {"chain": "bsc", "chain_id": 56, "native": False, "address": "0x55d398326f99059fF775485246999027B3197955"},
        "polygon": {"chain": "polygon", "chain_id": 137, "native": False, "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"}
    },
    FiatCurrency.USD: {"chain": "usd", "chain_id": "usd", "native": True, "address": "native"},
    FiatCurrency.NGN: {"chain": "ngn", "chain_id": "ngn", "native": True, "address": "native"},
    FiatCurrency.EUR: {"chain": "eur", "chain_id": "eur", "native": True, "address": "native"},
    FiatCurrency.GBP: {"chain": "gbp", "chain_id": "gbp", "native": True, "address": "native"}
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
        Symbols.DODGE: lambda: send_btc(req, symbol),
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

def get_swap_quote(
    from_chain: str,
    to_chain: str,
    from_token: str,
    to_token: str,
    amount: Decimal,
    from_address: str,
    to_address: Optional[str] = None,
    slippage: float = 0.5,
    order: str = "RECOMMENDED"
) -> Dict:
    """Get a quote for swapping tokens using LiFi."""
    try:
        try:
            if isinstance(amount, str):
                amount = Decimal(amount)
            # For native tokens (BNB/ETH), multiply by 10^18
            if from_token.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee":
                amount_wei = int(amount * Decimal(10**18))
            else:
                amount_wei = int(amount)
                
        except Exception as conv_ex:
            return {
                "success": False,
                "message": f"Invalid amount format: {str(conv_ex)}. Example valid amount: '1.5' for 1.5 BNB",
                "status_code": HTTPStatusCode.BAD_REQUEST
            }
        
        params = {
            "fromChain": from_chain,
            "toChain": to_chain,
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
                "message": f"LiFi API error1: {error_msg}",
                "status_code": result.get("status_code", HTTPStatusCode.BAD_REQUEST),
                "data": result.get("data")
            }
        
        # Add provider metadata to successful response
        if result.get("data"):
            result["data"]["provider"] = "lifi"
            result["data"]["quote_id"] = result["data"].get("id")
        
        return result
        
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

def execute_swap(
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
        # Step 1: Get the swap quote
        quote_result = get_swap_quote(
            from_chain=str(from_symbol),
            to_chain=str(to_symbol),
            from_token="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            to_token="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
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


# Fiat transaction functions (remain unchanged from your original code)
# def handle_fiat_transaction(
#     transaction_type: TransactionType,
#     crypto_symbol: Union[Symbols, str],
#     fiat_currency: FiatCurrency,
#     amount: Decimal,
#     wallet_address: str,
#     provider: Optional[BuySellProvider] = None,
#     email: Optional[str] = None,
#     phone: Optional[str] = None,
#     **extra_params
# ) -> Dict:
#     try:
#         crypto_symbol = convert_to_symbol(crypto_symbol)
#     except ValueError as e:
#         return {"success": False, "message": str(e), "status_code": HTTPStatusCode.BAD_REQUEST}
    
#     token_config = get_token_config(crypto_symbol)
#     if not token_config:
#         return {
#             "success": False,
#             "message": f"Unsupported token: {crypto_symbol}",
#             "status_code": HTTPStatusCode.BAD_REQUEST
#         }
    
#     params = {
#         "crypto_symbol": crypto_symbol.value,
#         "fiat_currency": fiat_currency.value,
#         "amount": str(amount),
#         "wallet_address": wallet_address,
#         "crypto_network": token_config.get("chain", "ethereum"),
#         "email": email,
#         "phone": phone,
#         "transaction_type": transaction_type.value,
#         **extra_params
#     }
    
#     provider = provider or determine_best_provider_for_fiat(crypto_symbol, fiat_currency)
    
#     quote_result = get_fiat_transaction_quote(params, provider)
#     if not quote_result.get("success", False):
#         return quote_result

#     except Exception as e:
#         return {"success": False, "message": f"Failed to execute swap: {str(e)}", "status_code": HTTPStatusCode.INTERNAL_SERVER_ERROR}
#     quote_id = quote_result.get("quote_id")
#     return execute_fiat_transaction(quote_id, params, provider)

def determine_best_provider_for_fiat(crypto_symbol: Symbols, fiat_currency: FiatCurrency) -> BuySellProvider:
    if fiat_currency == FiatCurrency.NGN:
        return BuySellProvider.KOTANIPAY
    if crypto_symbol in [Symbols.BTC, Symbols.ETH, Symbols.USDT]:
        return BuySellProvider.MOONPAY
    return BuySellProvider.PAYBIS

def get_fiat_transaction_quote(params: Dict, provider: BuySellProvider) -> Dict:
    is_buy = params["transaction_type"] == TransactionType.BUY.value
    
    if provider == BuySellProvider.PAYBIS:
        payload = {
            "currencyCodeFrom": params["fiat_currency"] if is_buy else params["crypto_symbol"],
            "currencyCodeTo": params["crypto_symbol"] if is_buy else params["fiat_currency"],
            "amount": params["amount"],
            "directionChange": "from",
            "isReceivedAmount": False
        }
        headers = {
            "Authorization": settings.PAYBIS_API_KEY,
            "Content-Type": "application/json"
        }
        result = api_request_handler("https://widget-api.paybis.com/v2/quote", "post", headers, payload)
        
    elif provider == BuySellProvider.KOTANIPAY:
        payload = {
            "fromCurrency": params["fiat_currency"] if is_buy else params["crypto_symbol"],
            "toCurrency": params["crypto_symbol"] if is_buy else params["fiat_currency"],
            "amount": params["amount"],
            "network": params["crypto_network"]
        }
        if params.get("email"):
            payload["email"] = params["email"]
        if params.get("phone"):
            payload["phoneNumber"] = params["phone"]
            
        headers = {
            "Authorization": f"Bearer {settings.KOTANIPAY_API_KEY}",
            "Content-Type": "application/json"
        }
        result = api_request_handler("https://api.kotanipay.com/v1/quote", "post", headers, payload)
        
    elif provider == BuySellProvider.TRANSAK:
        query_params = {
            "fiatCurrency": params["fiat_currency"],
            "cryptoCurrency": params["crypto_symbol"],
            "amount": params["amount"],
            "paymentMethod": "credit_debit_card" if is_buy else "crypto_wallet",
            "isBuyOrSell": "buy" if is_buy else "sell",
            "network": params["crypto_network"]
        }
        headers = {"X-API-KEY": settings.TRANSAK_API_KEY, "Content-Type": "application/json"}
        result = api_request_handler("https://api.transak.com/api/v2/currencies/price/quotes", "get", headers, None, query_params)
        
    elif provider == BuySellProvider.MOONPAY:
        query_params = {
            "baseCurrencyCode": params["crypto_symbol"].lower(),
            "quoteCurrencyCode": params["fiat_currency"].lower(),
            "baseCurrencyAmount" if not is_buy else "quoteCurrencyAmount": params["amount"],
            "areFeesIncluded": True
        }
        result = api_request_handler("https://api.moonpay.com/v3/currencies/quote", "get", None, None, query_params)
        
    else:
        return {
            "success": False,
            "message": f"Unsupported provider: {provider}",
            "status_code": HTTPStatusCode.BAD_REQUEST
        }
    
    result["provider"] = provider.value
    result["quote_id"] = result.get("data", {}).get("quoteId") or result.get("data", {}).get("id")
    return result

def execute_fiat_transaction(quote_id: str, params: Dict, provider: BuySellProvider) -> Dict:
    is_buy = params["transaction_type"] == TransactionType.BUY.value
    
    if provider == BuySellProvider.PAYBIS:
        payload = {
            "quote_id": quote_id,
            "from_currency": params["fiat_currency"] if is_buy else params["crypto_symbol"],
            "to_currency": params["crypto_symbol"] if is_buy else params["fiat_currency"],
            "amount": params["amount"]
        }
        
        if is_buy:
            payload["address"] = params["wallet_address"]
        else:
            payload["payout_details"] = {
                "account_number": params.get("bank_account", ""),
                "account_name": params.get("account_name", ""),
                "bank_code": params.get("bank_code", ""),
                "email": params.get("email", "")
            }
            
        headers = {
            "Authorization": settings.PAYBIS_API_KEY,
            "Content-Type": "application/json"
        }
        return api_request_handler("https://widget-api.paybis.com/v2/exchange", "post", headers, payload)
        
    elif provider == BuySellProvider.KOTANIPAY:
        payload = {
            "quoteId": quote_id,
            "network": params["crypto_network"]
        }
        
        if is_buy:
            payload.update({
                "fromCurrency": params["fiat_currency"],
                "toCurrency": params["crypto_symbol"],
                "destinationAddress": params["wallet_address"]
            })
        else:
            payload.update({
                "fromCurrency": params["crypto_symbol"],
                "toCurrency": params["fiat_currency"],
                "sourceAddress": params["wallet_address"],
                "bankDetails": {
                    "accountNumber": params.get("bank_account", ""),
                    "accountName": params.get("account_name", ""),
                    "bankCode": params.get("bank_code", "")
                }
            })
            
        headers = {
            "Authorization": f"Bearer {settings.KOTANIPAY_API_KEY}",
            "Content-Type": "application/json"
        }
        return api_request_handler("https://api.kotanipay.com/v1/transactions", "post", headers, payload)
        
    elif provider == BuySellProvider.TRANSAK:
        payload = {
            "quoteId": quote_id,
            "fiatCurrency": params["fiat_currency"],
            "cryptoCurrency": params["crypto_symbol"],
            "amount": params["amount"],
            "isBuyOrSell": "buy" if is_buy else "sell"
        }
        
        if is_buy:
            payload["walletAddress"] = params["wallet_address"]
            payload["paymentMethod"] = "credit_debit_card"
        else:
            payload["payoutMethod"] = "bank_transfer"
            payload["bankDetails"] = {
                "accountNumber": params.get("bank_account", ""),
                "accountHolderName": params.get("account_name", ""),
                "bankCode": params.get("bank_code", "")
            }
            
        if params.get("email"):
            payload["email"] = params["email"]
            
        headers = {"X-API-KEY": settings.TRANSAK_API_KEY, "Content-Type": "application/json"}
        return api_request_handler("https://api.transak.com/api/v2/orders/create", "post", headers, payload)
        
    elif provider == BuySellProvider.MOONPAY:
        payload = {
            "quoteId": quote_id,
            "externalCustomerId": params.get("email", f"user_{int(time.time())}"),
            "externalTransactionId": f"tx_{int(time.time())}"
        }
        
        if is_buy:
            payload["walletAddress"] = params["wallet_address"]
            payload["baseCurrencyCode"] = params["crypto_symbol"].lower()
            payload["quoteCurrencyCode"] = params["fiat_currency"].lower()
        else:
            payload["refundWalletAddress"] = params["wallet_address"]
            payload["bankDetails"] = {
                "accountNumber": params.get("bank_account", ""),
                "accountHolderName": params.get("account_name", ""),
                "bankCode": params.get("bank_code", "")
            }
            payload["baseCurrencyCode"] = params["fiat_currency"].lower()
            payload["quoteCurrencyCode"] = params["crypto_symbol"].lower()
            
        if params.get("email"):
            payload["email"] = params["email"]
            
        headers = {"Content-Type": "application/json"}
        return api_request_handler("https://api.moonpay.com/v1/transactions", "post", headers, payload)
        
    else:
        return {
            "success": False,
            "message": f"Unsupported provider: {provider}",
            "status_code": HTTPStatusCode.BAD_REQUEST
        }

def buy_crypto_with_fiat(
    crypto_symbol: Union[Symbols, str],
    fiat_currency: FiatCurrency,
    fiat_amount: Decimal,
    wallet_address: str,
    provider: Optional[BuySellProvider] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> WalletResponseDTO:
    try:
        result = handle_fiat_transaction(
            TransactionType.BUY,
            crypto_symbol,
            fiat_currency,
            fiat_amount,
            wallet_address,
            provider,
            email,
            phone
        )
        
        if result.get("success", False):
            return WalletResponseDTO(
                data=result.get("data"),
                message=f"Buy order created successfully with {result.get('provider')}"
            )
        return WalletResponseDTO(
            message=result.get("message", "Failed to create buy order"),
            success=False,
            status_code=result.get("status_code", HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def sell_crypto_for_fiat(
    crypto_symbol: Union[Symbols, str],
    fiat_currency: FiatCurrency,
    crypto_amount: Decimal,
    wallet_address: str,
    bank_account: str,
    account_name: str,
    bank_code: str,
    provider: Optional[BuySellProvider] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> WalletResponseDTO:
    try:
        extra_params = {
            "bank_account": bank_account,
            "account_name": account_name,
            "bank_code": bank_code
        }
        
        result = handle_fiat_transaction(
            TransactionType.SELL,
            crypto_symbol,
            fiat_currency,
            crypto_amount,
            wallet_address,
            provider,
            email,
            phone,
            **extra_params
        )
        
        if result.get("success", False):
            return WalletResponseDTO(
                data=result.get("data"),
                message=f"Sell order created successfully with {result.get('provider')}"
            )
        return WalletResponseDTO(
            message=result.get("message", "Failed to create sell order"),
            success=False,
            status_code=result.get("status_code", HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def get_available_payment_methods(
    provider: BuySellProvider,
    fiat_currency: Optional[FiatCurrency] = None
) -> WalletResponseDTO:
    try:
        endpoints = {
            BuySellProvider.PAYBIS: "https://widget-api.paybis.com/v2/payment-methods",
            BuySellProvider.KOTANIPAY: "https://api.kotanipay.com/v1/payment-methods",
            BuySellProvider.TRANSAK: "https://api.transak.com/api/v2/payment-methods",
            BuySellProvider.MOONPAY: "https://api.moonpay.com/v3/payment-methods"
        }
        
        headers = {}
        if provider == BuySellProvider.PAYBIS:
            headers = {
                "Authorization": settings.PAYBIS_API_KEY,
                "Content-Type": "application/json"
            }
        elif provider == BuySellProvider.KOTANIPAY:
            headers = {"Authorization": f"Bearer {settings.KOTANIPAY_API_KEY}"}
        elif provider == BuySellProvider.TRANSAK:
            headers = {"X-API-KEY": settings.TRANSAK_API_KEY}
        
        params = {}
        if fiat_currency:
            if provider == BuySellProvider.PAYBIS:
                params["currency"] = fiat_currency.value
            elif provider == BuySellProvider.KOTANIPAY:
                params["fiatCurrency"] = fiat_currency.value
            elif provider == BuySellProvider.TRANSAK:
                params["fiatCurrency"] = fiat_currency.value
            elif provider == BuySellProvider.MOONPAY:
                params["baseCurrency"] = fiat_currency.value.lower()
        
        endpoint = endpoints.get(provider)
        if not endpoint:
            return WalletResponseDTO(
                message=f"Unsupported provider: {provider}",
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            )
            
        result = api_request_handler(endpoint, "get", headers, None, params)
        
        if result.get("success", False):
            return WalletResponseDTO(
                data=result.get("data"),
                message=f"Available payment methods retrieved for {provider.value}"
            )
        return WalletResponseDTO(
            message=result.get("message", f"Failed to retrieve payment methods for {provider.value}"),
            success=False,
            status_code=result.get("status_code", HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def get_supported_currencies(
    provider: BuySellProvider,
    transaction_type: Optional[TransactionType] = None
) -> WalletResponseDTO:
    """Get supported currencies (both fiat and crypto) for a specific provider."""
    try:
        # Define endpoints for each provider
        endpoints = {
            BuySellProvider.PAYBIS: "https://widget-api.paybis.com/v2/currencies",
            BuySellProvider.KOTANIPAY: "https://api.kotanipay.com/v1/currencies",
            BuySellProvider.TRANSAK: "https://api.transak.com/api/v2/currencies",
            BuySellProvider.MOONPAY: "https://api.moonpay.com/v3/currencies"
        }
        
        # Define headers for each provider
        headers = {}
        if provider == BuySellProvider.PAYBIS:
            headers = {
                "X-API-KEY": settings.PAYBIS_API_KEY,
                "X-API-SECRET": settings.PAYBIS_SECRET_KEY
            }
        elif provider == BuySellProvider.KOTANIPAY:
            headers = {"Authorization": f"Bearer {settings.KOTANIPAY_API_KEY}"}
        elif provider == BuySellProvider.TRANSAK:
            headers = {"X-API-KEY": settings.TRANSAK_API_KEY}
        
        # Define query parameters
        params = {}
        if transaction_type:
            if provider == BuySellProvider.PAYBIS:
                params["type"] = transaction_type.value
            elif provider == BuySellProvider.KOTANIPAY:
                params["type"] = transaction_type.value
            elif provider == BuySellProvider.TRANSAK:
                params["isBuyOrSell"] = transaction_type.value
            elif provider == BuySellProvider.MOONPAY:
                params["transactionType"] = transaction_type.value
        
        # Make API request
        endpoint = endpoints.get(provider)
        if not endpoint:
            return WalletResponseDTO(
                message=f"Unsupported provider: {provider}",
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            )
            
        result = api_request_handler(endpoint, "get", headers, None, params)
        
        if result.get("success", False):
            return WalletResponseDTO(
                data=result.get("data"),
                message=f"Supported currencies retrieved for {provider.value}"
            )
        return WalletResponseDTO(
            message=result.get("message", f"Failed to retrieve currencies for {provider.value}"),
            success=False,
            status_code=result.get("status_code", HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )