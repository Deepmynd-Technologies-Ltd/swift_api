
from typing import List
from helper.generate_wallet import generate_mnemonic, generate_wallets_from_seed
from helper.send_transaction import send_bnb, send_btc, send_eth, send_sol, send_usdt
from helper.send_transaction.send_tron import send_trx
from helper.wallet_balance import get_bnb_balance_and_history, get_btc_balance_and_history, get_dodge_balance, get_eth_balance_and_history, get_sol_balance_and_history, get_tron_balance, get_usdt_balance
from helper.wallet_transaction import get_bnb_transactions, get_btc_transactions, get_dodge_transactions, get_eth_transactions, get_sol_transactions, get_trx_transactions, get_usdt_transactions
from home.wallet_schema import HTTPStatusCode, SendTransactionDTO, Symbols, TransactionsInfo, WalletInfoResponse, WalletResponseDTO

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
    return WalletResponseDTO(message=str(ex), success=False, status_code=HTTPStatusCode.BAD_REQUEST)

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
      Symbols.BTC: lambda: send_btc(req, symbols),
      Symbols.ETH: lambda: send_eth(req),
      Symbols.SOL: lambda: send_sol(req),
      Symbols.DODGE: lambda: send_btc(req, symbols),
      Symbols.BNB: lambda: send_bnb(req),
      Symbols.TRON: lambda: send_trx(req),
      Symbols.USDT: lambda: send_usdt(req),
    }
    value = switch.get(symbols)
    return WalletResponseDTO(data="Successful", message="Transaction sent")
  except Exception as ex:
    return WalletResponseDTO(message=str(ex), success=False, status_code=HTTPStatusCode.BAD_REQUEST)