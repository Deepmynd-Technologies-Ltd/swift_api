from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
from ninja import Router
from authentication.schemas import ResponseDTO
from wallet.schemas import CreateTransactionDTO
from wallet.services import send_eth


# Create your views here.

wallet_router = Router(tags=["Wallets"])

infura_url = 'https://mainnet.infura.io/v3/39e6e3a5da494a6fa2a72542cdcc9b38'
web3 = Web3(Web3.HTTPProvider(infura_url))

@wallet_router.post("/transfer", response={200: ResponseDTO, 400: ResponseDTO})
def transfer(request, req:CreateTransactionDTO):
    user = request.user
    res = send_eth(user, req=req)
    return wallet_router.api.create_response(request, res, status=res.status)