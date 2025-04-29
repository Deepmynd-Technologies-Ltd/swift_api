
import traceback
from typing import Dict, List, Optional
import requests
from django.conf import settings
from home.wallet_schema import Symbols, SendTransactionDTO, WalletResponseDTO
from helper.generate_wallet import generate_mnemonic, generate_wallets_from_seed
from helper.send_transaction.send_bnb import send_bnb
from helper.send_transaction.send_btc import send_btc
from helper.send_transaction.send_eth import send_eth
from helper.send_transaction.send_sol import send_sol
from helper.send_transaction.send_usdt import send_usdt_bep20
from helper.send_transaction.send_tron import send_trx
from helper.wallet_balance import get_bnb_balance_and_history, get_btc_balance_and_history, get_dodge_balance, get_eth_balance_and_history, get_sol_balance_and_history, get_tron_balance, get_usdt_balance
from helper.wallet_transaction import get_bnb_transactions, get_btc_transactions, get_dodge_transactions, get_eth_transactions, get_sol_transactions, get_trx_transactions, get_usdt_transactions
from home.wallet_schema import HTTPStatusCode, SendTransactionDTO, Symbols, TransactionsInfo, WalletInfoResponse, WalletResponseDTO


# Chain and token configuration
CHAIN_CONFIG = {
    Symbols.BNB: {"chain": "bsc", "native": True, "address": "0x0000000000000000000000000000000000000000"},
    Symbols.BTC: {"chain": "bitcoin", "native": True, "address": "native"},
    Symbols.DODGE: {"chain": "dogechain", "native": True, "address": "native"},
    Symbols.ETH: {"chain": "ethereum", "native": True, "address": "0x0000000000000000000000000000000000000000"},
    Symbols.SOL: {"chain": "solana", "native": True, "address": "So11111111111111111111111111111111111111112"},
    Symbols.USDT: {"chain": "bsc", "native": False, "address": "0x55d398326f99059fF775485246999027B3197955"},
}

def generate_secrete_phrases()->WalletResponseDTO[str]:
  try:
    phrases = generate_mnemonic()
    return WalletResponseDTO(data=phrases, message="Phrases generated")
  except Exception as ex:
    return WalletResponseDTO(message=str(ex), status_code=HTTPStatusCode.BAD_REQUEST, success=False)

def import_from_phrases(phrase:str)->WalletResponseDTO[List[WalletInfoResponse]]:
  try:
    val = generate_wallets_from_seed(phrase)
    return WalletResponseDTO(data=val, message="Wallet Generated")
  except Exception as ex:
    error_message = f"{str(ex)}\n{traceback.format_exc()}"
    return WalletResponseDTO(message=error_message, success=False, status_code=HTTPStatusCode.BAD_REQUEST)

def get_wallet_balance(symbols:Symbols, address:str)->WalletResponseDTO[float]:
  try:
    switch={
      Symbols.BTC: lambda: get_btc_balance_and_history(address=address),
      Symbols.ETH: lambda: get_eth_balance_and_history(address=address),
      Symbols.SOL: lambda: get_sol_balance_and_history(address=address),
      Symbols.DODGE: lambda: get_dodge_balance(address=address),
      Symbols.BNB: lambda: get_bnb_balance_and_history(address=address),
      Symbols.TRON: lambda: get_tron_balance(address=address),
      Symbols.USDT: lambda: get_usdt_balance(address=address),
    }
    value = switch.get(symbols, lambda: "Invalid Symbols")()

    if not isinstance(value, float):
      raise Exception("Invalid Symbol")

    return WalletResponseDTO(data=value, message="Ballance gotten")
  except Exception as ex:
    return WalletResponseDTO(message=str(ex), success=False, status_code=HTTPStatusCode.BAD_REQUEST)

def get_all_transactions_history(symbols:Symbols, address:str)-> WalletResponseDTO[List[TransactionsInfo]]:
  try:
    switch = {
      Symbols.BTC: lambda: get_btc_transactions(address),
      Symbols.ETH: lambda: get_eth_transactions(address),
      Symbols.SOL: lambda: get_sol_transactions(address),
      Symbols.DODGE: lambda: get_dodge_transactions(address),
      Symbols.BNB: lambda: get_bnb_transactions(address),
      Symbols.TRON: lambda: get_trx_transactions(address),
      Symbols.USDT: lambda: get_usdt_transactions(address),
      # Symbols.ETH: get_eth_transactions(address),
    }
    value = switch.get(symbols, lambda: "Invalid Symbols")()

    return WalletResponseDTO(data=value, message="Transaction List")
  except Exception as ex:
    return WalletResponseDTO(message=str(ex), success=False, status_code=HTTPStatusCode.BAD_REQUEST)

def send_crypto_transaction(symbols:Symbols, req:SendTransactionDTO)->WalletResponseDTO[str]:
  try:
    switch = {
      Symbols.BTC: lambda: send_btc(req),
      Symbols.ETH: lambda: send_eth(req),
      Symbols.SOL: lambda: send_sol(req),
      Symbols.DODGE: lambda: send_btc(req),
      Symbols.BNB: lambda: send_bnb(req),
      Symbols.TRON: lambda: send_trx(req),
      Symbols.USDT: lambda: send_usdt_bep20(req),
    }
    send_function = switch.get(symbols, None)
    
    if send_function is None:
      raise ValueError(f"Invalid symbol: {symbols}")

    send_function()
    return WalletResponseDTO(data="Successful", message="Transaction sent Successfully")
  except Exception as ex:
    error_message = f"{str(ex)}\n{traceback.format_exc()}"
    print(error_message)
    return WalletResponseDTO(message=error_message, success=False, status_code=HTTPStatusCode.BAD_REQUEST)


def get_swap_provider(from_chain: str, to_chain: str) -> str:
    """Determine the best swap provider based on chains"""
    return "Li.Fi" if from_chain != to_chain else "1inch"

def get_swap_quote(provider: str, params: Dict) -> Optional[Dict]:
    """Get swap quote from provider"""
    try:
        if provider == "1inch":
            url = f"https://api.1inch.io/v5.0/{params['chain_id']}/swap"
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        
        elif provider == "Li.Fi":
            url = "https://li.quest/v1/quote"
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        
    except Exception:
        return None

def swap_crypto_transaction(symbols: Symbols, req: SendTransactionDTO) -> WalletResponseDTO[str]:
    try:
        from_config = CHAIN_CONFIG.get(symbols)
        to_config = CHAIN_CONFIG.get(req.to_symbol)
        
        if not from_config or not to_config:
            return WalletResponseDTO(
                message="Unsupported token pair",
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            )

        # Determine swap provider
        provider = get_swap_provider(from_config["chain"], to_config["chain"])
        
        # Prepare swap parameters
        params = {
            "fromChain": from_config["chain"],
            "toChain": to_config["chain"],
            "fromToken": from_config["address"],
            "toToken": to_config["address"],
            "fromAmount": str(req.amount),
            "fromAddress": req.sender_address,
            "receiverAddress": req.receiver_address or req.sender_address,
            "slippage": req.slippage or 0.5,
        }

        if provider == "1inch":
            params.update({
                "chain_id": 56 if from_config["chain"] == "bsc" else 1,  # BSC or ETH
                "fromTokenAddress": from_config["address"],
                "toTokenAddress": to_config["address"],
            })
        
        # Get swap quote
        quote = get_swap_quote(provider, params)
        if not quote:
            return WalletResponseDTO(
                message="Failed to get swap quote",
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            )

        # For real implementation, you would prepare and return transaction data here
        # For this example, we'll just return success
        return WalletResponseDTO(
            data="Transaction data would be returned here",
            message="Swap prepared successfully. Sign the transaction in your wallet.",
            success=True
        )

    except Exception as ex:
        error_message = f"{str(ex)}\n{traceback.format_exc()}"
        print(error_message)
        return WalletResponseDTO(
            message=error_message,
            success=False,
            status_code=HTTPStatusCode.BAD_REQUEST
        )
