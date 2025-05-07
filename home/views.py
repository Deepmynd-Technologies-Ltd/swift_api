from typing import Dict, List, Optional
from ninja import Router
from helper.api_documentation import (
    first_description, second_description, 
    third_description, fourth_description, 
    fifth_description, swap_description
)
from helper.coingeko_api import get_coins_value
from home.wallet_schema import (
    PhraseRequest, SendTransactionDTO, Symbols, 
    TransactionsInfo, WalletInfoResponse, WalletResponseDTO,
    SwapQuoteRequest, SwapExecuteRequest, HTTPStatusCode
)
from home.wallet_services import (
    generate_secrete_phrases, import_from_phrases,
    get_wallet_balance, get_all_transactions_history,
    send_crypto_transaction, get_swap_quote, execute_swap
)

wallet_system = Router(tags=["Wallet Management"])

@wallet_system.get('/')
def test_ping(request):
    val = get_coins_value()
    return wallet_system.api.create_response(request, val, status=200)

@wallet_system.get('phrase/', response=WalletResponseDTO[str], 
                  description=first_description, summary="Generate Wallet Phrase")
def generate_wallet_phrase(request):
    res = generate_secrete_phrases()
    return wallet_system.api.create_response(request, res, status=res.status_code)

@wallet_system.post('generate_wallet/', response=WalletResponseDTO[List[WalletInfoResponse]], 
                   description=second_description, summary="Generate Wallet")
def generate_wallet(request, req: PhraseRequest):
    res = import_from_phrases(req.phrase)
    return wallet_system.api.create_response(request, res, status=res.status_code)

@wallet_system.get('get_balance/', response=WalletResponseDTO[float], 
                  description=third_description, summary="Get Balance")
def get_balance(request, symbol: Symbols, address: str):
    res = get_wallet_balance(symbol, address)
    return wallet_system.api.create_response(request, res, status=res.status_code)

@wallet_system.get('get_transaction/', response=WalletResponseDTO[List[TransactionsInfo]], 
                  description=fourth_description, summary="Get Transactions")
def get_transactions(request, symbol: Symbols, address: str):
    val = get_all_transactions_history(symbol, address)
    return wallet_system.api.create_response(request, val, status=val.status_code)

@wallet_system.post("send_transaction/", response=WalletResponseDTO[str], 
                   description=fifth_description, summary="Send Transactions")
def send_transactions(request, symbol: Symbols, req: SendTransactionDTO):
    val = send_crypto_transaction(symbol, req)
    return wallet_system.api.create_response(request, val, status=val.status_code)

@wallet_system.post("swap/quote/", response=WalletResponseDTO[Dict], 
                   description=swap_description, summary="Get Swap Quote")
def get_swap_quote_endpoint(request, req: SwapQuoteRequest):
    try:
        quote_result = get_swap_quote(
            from_symbol=req.from_symbol,
            to_symbol=req.to_symbol,
            amount=req.amount,
            from_address=req.from_address,
            to_address=req.to_address,
            slippage=req.slippage or 0.5,
            provider=req.provider
        )
        
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data=quote_result.get("data"),
                message=quote_result.get("message"),
                success=quote_result.get("success", False),
                status_code=quote_result.get("status_code", HTTPStatusCode.OK if quote_result.get("success", False) else HTTPStatusCode.BAD_REQUEST)
            ),
            status=quote_result.get("status_code", HTTPStatusCode.OK if quote_result.get("success", False) else HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        error_message = f"Failed to get swap quote: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.post("swap/execute/", response=WalletResponseDTO[Dict],
                   description=swap_description, summary="Execute Token Swap")
def execute_swap_endpoint(request, req: SwapExecuteRequest):
    try:
        execution_result = execute_swap(
            quote_id=req.quote_id,
            from_symbol=req.from_symbol,
            to_symbol=req.to_symbol,
            amount=req.amount,
            from_address=req.from_address,
            to_address=req.to_address,
            slippage=req.slippage or 0.5,
            provider=req.provider
        )
        
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data=execution_result.get("data"),
                message=execution_result.get("message"),
                success=execution_result.get("success", False),
                status_code=execution_result.get("status_code", HTTPStatusCode.OK if execution_result.get("success", False) else HTTPStatusCode.BAD_REQUEST)
            ),
            status=execution_result.get("status_code", HTTPStatusCode.OK if execution_result.get("success", False) else HTTPStatusCode.BAD_REQUEST)
        )
    except Exception as ex:
        error_message = f"Failed to execute swap: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )