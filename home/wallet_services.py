import traceback
from typing import Dict, List, Optional
import requests
from decimal import Decimal
from enum import Enum
from django.conf import settings
import time
from home.wallet_schema import (
    Symbols, SendTransactionDTO, WalletResponseDTO, HTTPStatusCode,
    TransactionsInfo, WalletInfoResponse, SwapProvider
)
from helper.generate_wallet import generate_mnemonic, generate_wallets_from_seed
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

# Chain IDs and Token Configurations
CHAIN_IDS = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "solana": "solana",
    "bitcoin": "bitcoin",
    "tron": "tron",
    "dogechain": "doge",
    "africa": "africa"
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
    }
}

# Wallet Core Functions
def generate_secrete_phrases() -> WalletResponseDTO[str]:
    try:
        phrases = generate_mnemonic()
        return WalletResponseDTO(data=phrases, message="Phrases generated")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            status_code=HTTPStatusCode.BAD_REQUEST,
            success=False
        )

def import_from_phrases(phrase: str) -> WalletResponseDTO[List[WalletInfoResponse]]:
    try:
        val = generate_wallets_from_seed(phrase)
        return WalletResponseDTO(data=val, message="Wallet Generated")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def get_wallet_balance(symbol: Symbols, address: str) -> WalletResponseDTO[float]:
    try:
        balance_handlers = {
            Symbols.BTC: get_btc_balance_and_history,
            Symbols.ETH: get_eth_balance_and_history,
            Symbols.SOL: get_sol_balance_and_history,
            Symbols.DODGE: get_dodge_balance,
            Symbols.BNB: get_bnb_balance_and_history,
            Symbols.TRON: get_tron_balance,
            Symbols.USDT: get_usdt_balance,
        }
        
        handler = balance_handlers.get(symbol)
        if not handler:
            raise ValueError("Invalid symbol")
            
        value = handler(address=address)
        if not isinstance(value, float):
            raise Exception("Invalid balance response")
            
        return WalletResponseDTO(data=value, message="Balance retrieved")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def get_all_transactions_history(symbol: Symbols, address: str) -> WalletResponseDTO[List[TransactionsInfo]]:
    try:
        tx_handlers = {
            Symbols.BTC: get_btc_transactions,
            Symbols.ETH: get_eth_transactions,
            Symbols.SOL: get_sol_transactions,
            Symbols.DODGE: get_dodge_transactions,
            Symbols.BNB: get_bnb_transactions,
            Symbols.TRON: get_trx_transactions,
            Symbols.USDT: get_usdt_transactions,
        }
        
        handler = tx_handlers.get(symbol)
        if not handler:
            raise ValueError("Invalid symbol")
            
        transactions = handler(address)
        return WalletResponseDTO(data=transactions, message="Transaction list retrieved")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

def send_crypto_transaction(symbol: Symbols, req: SendTransactionDTO) -> WalletResponseDTO[str]:
    try:
        tx_handlers = {
            Symbols.BTC: lambda: send_btc(req, symbol),
            Symbols.ETH: lambda: send_eth(req),
            Symbols.SOL: lambda: send_sol(req),
            Symbols.DODGE: lambda: send_btc(req, symbol),
            Symbols.BNB: lambda: send_bnb(req),
            Symbols.TRON: lambda: send_trx(req),
            Symbols.USDT: lambda: send_usdt_bep20(req),
        }
        
        handler = tx_handlers.get(symbol)
        if not handler:
            raise ValueError("Invalid symbol")
            
        handler()
        return WalletResponseDTO(data="Successful", message="Transaction sent")
    except Exception as ex:
        return WalletResponseDTO(
            message=str(ex),
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )

# Swap Service Functions
def determine_best_provider(from_symbol: Symbols, to_symbol: Symbols) -> SwapProvider:
    """Determine the best swap provider based on token pair."""
    from_config = TOKEN_CONFIG.get(from_symbol)
    to_config = TOKEN_CONFIG.get(to_symbol)
    
    if isinstance(from_config, dict) and "chain" not in from_config:
        from_config = from_config.get("bsc")
    
    if isinstance(to_config, dict) and "chain" not in to_config:
        to_config = to_config.get("bsc")
    
    if from_symbol.value.lower() in ['usd', 'eur', 'gbp'] or to_symbol.value.lower() in ['usd', 'eur', 'gbp']:
        return SwapProvider.TRANSAK
    
    if (from_config.get("chain") == "africa" or to_config.get("chain") == "africa"):
        return SwapProvider.KOTANIPAY
    
    return SwapProvider.PAYBIS

def get_paybis_quote(params: Dict) -> Dict:
    """Get swap quote from Paybis API"""
    try:
        # Paybis API requires authentication
        api_key = settings.PAYBIS_API_KEY
        secret_key = settings.PAYBIS_SECRET_KEY
        
        payload = {
            "from_currency": params["from_symbol"],
            "to_currency": params["to_symbol"],
            "amount": params["amount"],
            "address": params["from_address"],
            "refund_address": params["from_address"],
            "extra_id": None  # For coins that need memo/tag
        }
        
        headers = {
            "X-API-KEY": api_key,
            "X-API-SECRET": secret_key,
            "Content-Type": "application/json"
        }
        
        url = "https://api.paybis.com/v2/public/exchange/calculate"
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "provider": "paybis",
                "quote_id": response.json().get("id"),
                "message": "Paybis quote retrieved"
            }
        else:
            return {
                "success": False,
                "message": f"Paybis API error: {response.text}",
                "status_code": response.status_code
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error calling Paybis API: {str(ex)}",
            "status_code": 500
        }

def get_kotanipay_quote(params: Dict) -> Dict:
    """Get quote from KotaniPay API (specialized for African markets)"""
    try:
        # KotaniPay API requires authentication
        api_key = settings.KOTANIPAY_API_KEY
        
        payload = {
            "fromCurrency": params["from_symbol"],
            "toCurrency": params["to_symbol"],
            "amount": params["amount"],
            "address": params["from_address"],
            "network": params.get("from_chain", "ethereum")  # Default to Ethereum
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = "https://api.kotanipay.com/v1/quote"
        
        if not settings.KOTANIPAY_API_KEY:
            mock_response = {
                "success": True,
                "data": {
                    "quoteId": "kotanipay-mock-quote",
                    "fromAmount": params["amount"],
                    "toAmount": float(params["amount"]) * 0.95,  # 5% fee
                    "fee": float(params["amount"]) * 0.05,
                    "rate": 0.95,
                    "provider": "kotanipay",
                    "expiresIn": 300  # 5 minutes
                },
                "message": "Quote retrieved successfully (simulated)"
            }
            return mock_response
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "provider": "kotanipay",
                "quote_id": response.json().get("quoteId"),
                "message": "KotaniPay quote retrieved"
            }
        else:
            return {
                "success": False,
                "message": f"KotaniPay API error: {response.text}",
                "status_code": response.status_code
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error calling KotaniPay API: {str(ex)}",
            "status_code": 500
        }

def get_transak_quote(params: Dict) -> Dict:
    """Get quote from Transak API (best for fiat integration)"""
    try:
        # Transak API requires authentication
        api_key = settings.TRANSAK_API_KEY
        
        payload = {
            "fiatCurrency": params["from_symbol"] if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else params["to_symbol"],
            "cryptoCurrency": params["to_symbol"] if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else params["from_symbol"],
            "amount": params["amount"],
            "paymentMethod": "credit_debit_card",  # Could be parameterized
            "isBuyOrSell": "buy" if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else "sell",
            "network": params.get("to_chain" if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else "from_chain", "ethereum")
        }
        
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        url = "https://api.transak.com/api/v2/currencies/price"
        
        if not settings.TRANSAK_API_KEY:
            mock_response = {
                "success": True,
                "data": {
                    "quoteId": "transak-mock-quote",
                    "fiatAmount": params["amount"] if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else float(params["amount"]) * 1000,
                    "cryptoAmount": float(params["amount"]) * 0.98 if params["from_symbol"] in ['USD', 'EUR', 'GBP'] else params["amount"],
                    "fee": float(params["amount"]) * 0.02,
                    "rate": 0.98,
                    "provider": "transak",
                    "validUntil": int(time.time()) + 300  # 5 minutes
                },
                "message": "Quote retrieved successfully (simulated)"
            }
            return mock_response
        
        response = requests.get(url, headers=headers, params=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "provider": "transak",
                "quote_id": response.json().get("quoteId"),
                "message": "Transak quote retrieved"
            }
        else:
            return {
                "success": False,
                "message": f"Transak API error: {response.text}",
                "status_code": response.status_code
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error calling Transak API: {str(ex)}",
            "status_code": 500
        }

def execute_paybis_swap(quote_id: str, params: Dict) -> Dict:
    """Execute a swap using Paybis"""
    try:
        api_key = settings.PAYBIS_API_KEY
        secret_key = settings.PAYBIS_SECRET_KEY
        
        payload = {
            "quote_id": quote_id,
            "from_currency": params["from_symbol"],
            "to_currency": params["to_symbol"],
            "amount": params["amount"],
            "address": params["to_address"] or params["from_address"],
            "refund_address": params["from_address"]
        }
        
        headers = {
            "X-API-KEY": api_key,
            "X-API-SECRET": secret_key,
            "Content-Type": "application/json"
        }
        
        url = "https://api.paybis.com/v2/public/exchange/create"
        
        if not settings.PAYBIS_API_KEY or not settings.PAYBIS_SECRET_KEY:
            mock_response = {
                "success": True,
                "data": {
                    "transaction_id": "paybis-mock-tx",
                    "status": "pending",
                    "from_amount": params["amount"],
                    "to_amount": float(params["amount"]) * 0.97,
                    "provider": "paybis"
                },
                "message": "Swap initiated successfully (simulated)"
            }
            return mock_response
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "message": "Paybis swap executed"
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error executing Paybis swap: {str(ex)}",
            "status_code": 500
        }

def execute_kotanipay_swap(quote_id: str, params: Dict) -> Dict:
    """Execute a swap using KotaniPay"""
    try:
        api_key = settings.KOTANIPAY_API_KEY
        
        payload = {
            "quoteId": quote_id,
            "fromCurrency": params["from_symbol"],
            "toCurrency": params["to_symbol"],
            "amount": params["amount"],
            "destinationAddress": params["to_address"] or params["from_address"],
            "network": params.get("to_chain", "ethereum")
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = "https://api.kotanipay.com/v1/swap"
        
        if not settings.TRANSAK_API_KEY:
            mock_response = {
                "success": True,
                "data": {
                    "transactionId": "kotanipay-mock-tx",
                    "status": "processing",
                    "fromAmount": params["amount"],
                    "toAmount": float(params["amount"]) * 0.95,
                    "provider": "kotanipay"
                },
                "message": "Swap initiated successfully (simulated)"
            }
        return mock_response
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "message": "KotaniPay swap executed"
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error executing KotaniPay swap: {str(ex)}",
            "status_code": 500
        }

def execute_transak_swap(quote_id: str, params: Dict) -> Dict:
    """Execute a fiat-to-crypto or crypto-to-fiat swap using Transak"""
    try:
        api_key = settings.TRANSAK_API_KEY
        
        is_buy = params["from_symbol"] in ['USD', 'EUR', 'GBP']
        
        payload = {
            "quoteId": quote_id,
            "fiatCurrency": params["from_symbol"] if is_buy else params["to_symbol"],
            "cryptoCurrency": params["to_symbol"] if is_buy else params["from_symbol"],
            "amount": params["amount"],
            "walletAddress": params["to_address"] if is_buy else params["from_address"],
            "paymentMethod": "credit_debit_card",
            "isBuyOrSell": "buy" if is_buy else "sell"
        }
        
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        url = "https://api.transak.com/api/v2/orders/create"
        
        if not settings.TRANSAK_API_KEY:
            mock_response = {
                "success": True,
                "data": {
                    "orderId": "transak-mock-order",
                    "status": "pending",
                    "fiatAmount": params["amount"] if is_buy else float(params["amount"]) * 1000,
                    "cryptoAmount": float(params["amount"]) * 0.98 if is_buy else params["amount"],
                    "provider": "transak"
                },
                "message": "Swap order created successfully (simulated)"
            }
            return mock_response
        
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "message": "Transak swap executed"
            }
    except Exception as ex:
        return {
            "success": False,
            "message": f"Error executing Transak swap: {str(ex)}",
            "status_code": 500
        }

def get_swap_quote(from_symbol: Symbols, to_symbol: Symbols, amount: Decimal, 
                  from_address: str, to_address: Optional[str] = None,
                  slippage: float = 0.5, provider: Optional[SwapProvider] = None) -> Dict:
    """Get a quote for swapping tokens."""
    from_config = TOKEN_CONFIG.get(from_symbol)
    to_config = TOKEN_CONFIG.get(to_symbol)
    
    if isinstance(from_config, dict) and "chain" not in from_config:
        from_config = from_config.get("bsc")
    
    if isinstance(to_config, dict) and "chain" not in to_config:
        to_config = to_config.get("bsc")
    
    if not from_config or not to_config:
        return {
            "success": False,
            "message": "Unsupported token pair",
            "status_code": HTTPStatusCode.BAD_REQUEST
        }
    
    if not provider:
        provider = determine_best_provider(from_symbol, to_symbol)
    
    params = {
        "from_symbol": from_symbol.value,
        "to_symbol": to_symbol.value,
        "from_chain": from_config["chain"],
        "to_chain": to_config["chain"],
        "from_token_address": from_config["address"],
        "to_token_address": to_config["address"],
        "chain_id": from_config["chain_id"],
        "amount": str(amount),
        "from_address": from_address,
        "to_address": to_address or from_address,
        "slippage": slippage
    }
    
    if provider == SwapProvider.PAYBIS:
        return get_paybis_quote(params)
    elif provider == SwapProvider.KOTANIPAY:
        return get_kotanipay_quote(params)
    elif provider == SwapProvider.TRANSAK:
        return get_transak_quote(params)
    else:
        return {
            "success": False,
            "message": f"Unsupported provider: {provider}",
            "status_code": HTTPStatusCode.BAD_REQUEST
        }

def execute_swap(quote_id: str, from_symbol: Symbols, to_symbol: Symbols, 
                amount: Decimal, from_address: str, to_address: Optional[str] = None,
                slippage: float = 0.5, provider: SwapProvider = None) -> Dict:
    """Execute a token swap."""
    params = {
        "from_symbol": from_symbol.value if from_symbol else None,
        "to_symbol": to_symbol.value if to_symbol else None,
        "amount": amount,
        "from_address": from_address,
        "to_address": to_address or from_address,
        "slippage": slippage
    }
    
    if provider == SwapProvider.PAYBIS:
        return execute_paybis_swap(quote_id, params)
    elif provider == SwapProvider.KOTANIPAY:
        return execute_kotanipay_swap(quote_id, params)
    elif provider == SwapProvider.TRANSAK:
        return execute_transak_swap(quote_id, params)
    else:
        return {
            "success": False,
            "message": f"Unsupported provider: {provider}",
            "status_code": HTTPStatusCode.BAD_REQUEST
        }