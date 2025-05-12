from typing import Dict, List, Optional
from ninja import Router
from decimal import Decimal
from helper.api_documentation import (
    first_description, second_description, 
    third_description, fourth_description, 
    fifth_description, swap_description,
    buy_crypto_description, sell_crypto_description,
    payment_methods_description, currencies_description
)
from helper.coingeko_api import get_coins_value
from home.wallet_schema import (
    PhraseRequest, SendTransactionDTO, Symbols, 
    TransactionsInfo, WalletInfoResponse, WalletResponseDTO,
    SwapQuoteRequest, SwapExecuteRequest, HTTPStatusCode,
    FiatCurrency, TransactionType, BuySellProvider,
    BuyCryptoRequest, SellCryptoRequest,
    PaymentMethodsRequest, CurrenciesRequest
)
from home.wallet_services import (
    generate_secrete_phrases, import_from_phrases,
    get_wallet_balance, get_all_transactions_history,
    send_crypto_transaction, get_swap_quote, execute_swap,
    get_swap_status,
    buy_crypto_with_fiat, sell_crypto_for_fiat,
    get_available_payment_methods, get_supported_currencies
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

@wallet_system.post("swap/execute/", response=WalletResponseDTO[Dict],
description="Execute a token swap in one step", summary="Execute Token Swap")
def execute_swap_endpoint(request, req: SwapExecuteRequest):
    try:
        # Execute the swap using the unified function
        swap_result = execute_swap(
            from_symbol=req.from_symbol,
            to_symbol=req.to_symbol,
            amount=req.amount,
            from_address=req.from_address,
            to_address=req.to_address,
            slippage=req.slippage or 0.5,
            order="RECOMMENDED"
        )

        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data=swap_result.get("data"),
                message=swap_result.get("message"),
                success=swap_result.get("success", False),
                status_code=swap_result.get("status_code", HTTPStatusCode.OK)
            ),
            status=swap_result.get("status_code", HTTPStatusCode.OK)
        )
    except Exception as ex:
        error_message = f"Failed to execute swap in views: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.get("swap/status/", response=WalletResponseDTO[Dict],
                  description="Get status of a swap transaction", 
                  summary="Get Swap Status")
def get_swap_status_endpoint(request, tx_hash: str):
    try:
        status_result = get_swap_status(tx_hash)
        
        response_data = {
            "data": status_result.get("data"),
            "message": status_result.get("message", 
                        "Transaction status retrieved successfully" if status_result.get("success") else "Failed to get transaction status"),
            "success": status_result.get("success", False),
            "status_code": status_result.get("status_code",
                          HTTPStatusCode.OK if status_result.get("success") else HTTPStatusCode.BAD_REQUEST)
        }

        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(**response_data),
            status=response_data["status_code"]
        )

    except Exception as ex:
        error_message = f"Failed to get swap status: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )
        
@wallet_system.post("buy/", response=WalletResponseDTO[Dict],
                   description=buy_crypto_description, summary="Buy Crypto with Fiat")
def buy_crypto_endpoint(request, req: BuyCryptoRequest):
    try:
        result = buy_crypto_with_fiat(
            crypto_symbol=req.crypto_symbol,
            fiat_currency=req.fiat_currency,
            fiat_amount=req.amount,
            wallet_address=req.wallet_address,
            provider=req.provider,
            email=req.email,
            phone=req.phone
        )
        
        return wallet_system.api.create_response(
            request,
            result,
            status=result.status_code
        )
    except Exception as ex:
        error_message = f"Failed to process buy order: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.post("sell/", response=WalletResponseDTO[Dict],
                   description=sell_crypto_description, summary="Sell Crypto for Fiat")
def sell_crypto_endpoint(request, req: SellCryptoRequest):
    try:
        result = sell_crypto_for_fiat(
            crypto_symbol=req.crypto_symbol,
            fiat_currency=req.fiat_currency,
            crypto_amount=req.amount,
            wallet_address=req.wallet_address,
            bank_account=req.bank_account,
            account_name=req.account_name,
            bank_code=req.bank_code,
            provider=req.provider,
            email=req.email,
            phone=req.phone
        )
        
        return wallet_system.api.create_response(
            request,
            result,
            status=result.status_code
        )
    except Exception as ex:
        error_message = f"Failed to process sell order: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.post("payment-methods/", response=WalletResponseDTO[Dict],
                   description=payment_methods_description, summary="Get Available Payment Methods")
def get_payment_methods_endpoint(request, req: PaymentMethodsRequest):
    try:
        result = get_available_payment_methods(
            provider=req.provider,
            fiat_currency=req.fiat_currency
        )
        
        return wallet_system.api.create_response(
            request,
            result,
            status=result.status_code
        )
    except Exception as ex:
        error_message = f"Failed to get payment methods: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.post("currencies/", response=WalletResponseDTO[Dict],
                   description=currencies_description, summary="Get Supported Currencies")
def get_currencies_endpoint(request, req: CurrenciesRequest):
    try:
        result = get_supported_currencies(
            provider=req.provider,
            transaction_type=req.transaction_type
        )
        
        return wallet_system.api.create_response(
            request,
            result,
            status=result.status_code
        )
    except Exception as ex:
        error_message = f"Failed to get supported currencies: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )