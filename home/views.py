# views.py
from typing import List
from ninja import Router

from helper.api_documentation import first_description, second_description, third_description, fourth_description, fifth_description
from helper.coingeko_api import get_coins_value
from home.wallet_schema import PhraseRequest, SendTransactionDTO, Symbols, TransactionsInfo, WalletInfoResponse, WalletResponseDTO
from home.wallet_services import generate_secrete_phrases, get_all_transactions_history, get_wallet_balance, import_from_phrases, send_crypto_transaction

wallet_system = Router(tags=["Wallet Address"])

"""
Task
1. Generate wallet address ☑️ {BNB, ETH, SOL, BTC, TRON, XRP and DODGE} {XRP is not included}
2. Import wallet addresses ☑️
3. Get wallet balances based on selected currency rate ☑️
4. Get wallet transactions {BTC, DODGE, BNB, ETH, SOL, TRON, } ☑️
5. Send crypto {BTC, DODGE, BNB, ETH, SOL, TRON, } ☑️
6. Swap between crypto
"""

@wallet_system.get('/')
def test_ping(request):
  val = get_coins_value()

  return wallet_system.api.create_response(request, val, status=200)

@wallet_system.get('phrase/', response=WalletResponseDTO[str], description= first_description, summary="Generate Wallet Phrase")
def generate_wallet_phrase(request):
  res = generate_secrete_phrases()
  return wallet_system.api.create_response(request, res, status=res.status_code)

@wallet_system.post('generate_wallet/', response=WalletResponseDTO[List[WalletInfoResponse]], description= second_description, summary="Generate Wallet")
def generate_wallet(request, req:PhraseRequest):
  res = import_from_phrases(req.phrase)
  print(res)
  return wallet_system.api.create_response(request, res, status=res.status_code)

@wallet_system.get('get_balance/', response=WalletResponseDTO[float], description=third_description, summary="Get Balance")
def get_balance(request, symbol:Symbols, address:str):
  res = get_wallet_balance(symbol,address)
  return wallet_system.api.create_response(request,res, status=res.status_code)

@wallet_system.get('get_transaction/', response=WalletResponseDTO[List[TransactionsInfo]], description=fourth_description, summary="Get Transactions")
def get_transactions(request, symbol:Symbols, address:str):
  val = get_all_transactions_history(symbol, address)
  return wallet_system.api.create_response(request, val, status=val.status_code)

@wallet_system.post("send_transaction/", response=WalletResponseDTO[str], description=fifth_description, summary="Send Transactions")
def send_transactions(request, symbol:Symbols, req:SendTransactionDTO):
  val = send_crypto_transaction(symbol, req)
  return wallet_system.api.create_response(request, val, status=val.status_code)