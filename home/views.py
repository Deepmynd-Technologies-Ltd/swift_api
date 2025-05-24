from typing import Dict, List, Optional
from ninja import Router
from decimal import Decimal
from django.conf import settings
from helper.api_documentation import (
    first_description, second_description, 
    third_description, fourth_description, 
    fifth_description,
    sixth_description, seventh_description,
    eight_description, ninth_description
)
from helper.coingeko_api import get_coins_value
from home.wallet_schema import (
    PhraseRequest, SendTransactionDTO, Symbols, 
    TransactionsInfo, WalletInfoResponse, WalletResponseDTO,
    SwapQuoteRequest, SwapExecuteRequest, HTTPStatusCode,
    PaybisTransactionRequest, TransakTransactionRequest, MoonPayTransactionRequest
)
from home.wallet_services import (
    generate_secrete_phrases, import_from_phrases,
    get_wallet_balance, get_all_transactions_history,
    send_crypto_transaction, get_swap_quote, prepare_swap,
    process_swap, get_swap_status, get_swap_quote,
)
from home.buy_sell import (
        process_paybis_transaction, process_transak_transaction,
        process_moonpay_transaction,
)

wallet_system = Router(tags=["Wallet Management"])


# Add this constant at the top of your file
WEB3_PROVIDER_URLS = {
    "ETH": f"https://mainnet.infura.io/v3/{settings.INFURA}",
    "BNB": "https://bsc-dataseed.binance.org/",
    "MATIC": "https://polygon-rpc.com",
    "SEPOLIA": f"https://sepolia.infura.io/v3/{settings.INFURA}",
    "BSC_TEST": "https://data-seed-prebsc-1-s1.binance.org:8545/",
    "USDT": f"https://mainnet.infura.io/v3/{settings.INFURA}",
    "USDC": f"https://mainnet.infura.io/v3/{settings.INFURA}",
    "DAI": f"https://mainnet.infura.io/v3/{settings.INFURA}",
    "SOL": "https://api.mainnet-beta.solana.com",
    "DODGE": "https://bsc-dataseed.binance.org/",
    "AVAX": "https://api.avax.network/ext/bc/C/rpc",
    "FTM": "https://rpc.ftm.tools",
    "ARB": "https://arb1.arbitrum.io/rpc",
    "OP": "https://mainnet.optimism.io",
    "BTC": f"https://mainnet.infura.io/v3/{settings.INFURA}",
}

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

def get_provider_url_for_token(token_symbol: str) -> str:
    """
    Get the appropriate web3 provider URL for a given token symbol.
    Defaults to Ethereum mainnet if no specific match is found.
    """
    token_symbol_upper = token_symbol.upper()
    return WEB3_PROVIDER_URLS.get(token_symbol_upper, WEB3_PROVIDER_URLS["ETH"])

@wallet_system.post("swap/quote/", response=WalletResponseDTO[Dict],
                    description="Get Swap Quote", 
                    summary="Get Swap Quote")
def get_swap_quote_endpoint(request, req: SwapQuoteRequest):
    try:

        # Fetch the swap quote
        swap_quote = get_swap_quote(
            from_symbol=req.from_symbol,
            to_symbol=req.to_symbol,
            from_address=req.from_address,
            to_address=req.to_address,
            amount=req.amount,
            slippage=req.slippage or 0.5,
            order="RECOMMENDED",
        )
        
        # Build the response data structure
        response_data = {
            "data": swap_quote.get("data"),
            "quote_data": swap_quote.get("quote_data"),
            "message": swap_quote.get("message"),
            "success": swap_quote.get("success", False),
            "status_code": swap_quote.get("status_code", HTTPStatusCode.OK)
        }

        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(**response_data),
            status=response_data["status_code"]
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

@wallet_system.post("swap/", response=WalletResponseDTO, description=sixth_description, summary="Process Token Swap")
def process_swap_endpoint(request, req: SwapExecuteRequest):
   
    try:
        # Determine if we should execute based on presence of private key
        execute = bool(req.private_key)
        
        # Get the appropriate web3 provider URL based on the from_symbol
        web3_provider_url = get_provider_url_for_token(req.from_symbol)
        
        # Process the swap with appropriate execution flag
        swap_result = process_swap(
            from_symbol=req.from_symbol,
            to_symbol=req.to_symbol,
            amount=req.amount,
            from_address=req.from_address,
            to_address=req.to_address,
            slippage=req.slippage or 0.5,
            order="RECOMMENDED",
            execute=execute,
            private_key=req.private_key if execute else None,
            web3_provider_url=web3_provider_url if execute else None,
            gas_multiplier=req.gas_multiplier or 1.1
        )
        
        # Build the response data structure
        response_data = {
            "data": swap_result.get("data"),
            "quote_data": swap_result.get("quote_data"),
            "message": swap_result.get("message"),
            "success": swap_result.get("success", False),
            "status_code": swap_result.get("status_code", HTTPStatusCode.OK)
        }

        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(**response_data),
            status=response_data["status_code"]
        )
        
    except Exception as ex:
        error_message = f"Failed to process swap in views: {str(ex)}"
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
        
@wallet_system.post("paybis/transaction/", response=WalletResponseDTO[Dict],
                  description=seventh_description, 
                  summary="Paybis Transaction Processing")
def paybis_transaction_endpoint(request, req: PaybisTransactionRequest):
    try:        
        # Process the Paybis transaction
        result = process_paybis_transaction(
            from_currency_or_crypto=req.from_currency_or_crypto,
            to_currency_or_crypto=req.to_currency_or_crypto,
            amount=req.amount,
            partner_user_id=req.partner_user_id,
            email=req.email,
            direction=req.direction,
            locale=req.locale
        )
        
        # Build the response based on the result
        status_code = result.get("status_code", 
                               HTTPStatusCode.OK if result.get("success", False) 
                               else HTTPStatusCode.BAD_REQUEST)
        
        response_data = {
            "widget_url": result.get("widget_url"),
            "quote_response": result.get("quote_response"),
            "transaction_type": result.get("transaction_type"),
            "request_id": result.get("request_id")
        } if result.get("success") else None
        
        response_dto = WalletResponseDTO(
            data=response_data,
            message=result.get("message", "Transaction processed successfully"),
            success=result.get("success", False),
            status_code=status_code,
        )

        return wallet_system.api.create_response(
            request,
            response_dto,
            status=status_code
        )
        
    except Exception as ex:
        error_message = f"Failed to process Paybis transaction: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )
        

@wallet_system.post("transak/transaction/", response=WalletResponseDTO[Dict],
                  description=eight_description, 
                  summary="Transak Transaction Processing")
def transak_transaction_endpoint(request, req: TransakTransactionRequest):
    try:        
        # Process the Transak transaction
        result = process_transak_transaction(
            from_currency_or_crypto=req.from_currency_or_crypto,
            to_currency_or_crypto=req.to_currency_or_crypto,
            amount=req.amount,
            wallet_address=req.wallet_address,
            direction=req.direction,
            locale=req.locale,
            user_data=req.user_data
        )
        
        # Build the response based on the result
        status_code = result.get("status_code", 
                               HTTPStatusCode.OK if result.get("success", False) 
                               else HTTPStatusCode.BAD_REQUEST)
        
        response_data = {
            "widget_url": result.get("widget_url"),
            "transaction_type": result.get("transaction_type"),
        } if result.get("success") else None
        
        response_dto = WalletResponseDTO(
            data=response_data,
            message=result.get("message", "Transaction processed successfully"),
            success=result.get("success", False),
            status_code=status_code,
        )

        return wallet_system.api.create_response(
            request,
            response_dto,
            status=status_code
        )
        
    except Exception as ex:
        error_message = f"Failed to process Transak transaction: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.post("moonpay/transaction/", response=WalletResponseDTO[Dict],
                  description=eight_description, 
                  summary="MoonPay Transaction Processing")
def moonpay_transaction_endpoint(request, req: MoonPayTransactionRequest):
    try:        
        # Process the MoonPay transaction
        result = process_moonpay_transaction(
            from_currency_or_crypto=req.from_currency_or_crypto,
            to_currency_or_crypto=req.to_currency_or_crypto,
            amount=req.amount,
            wallet_address=req.wallet_address,
            direction=req.direction,
            locale=req.locale,
            user_data=req.user_data
        )
        
        # Build the response based on the result
        status_code = result.get("status_code", 
                               HTTPStatusCode.OK if result.get("success", False) 
                               else HTTPStatusCode.BAD_REQUEST)
        
        response_data = {
            "widget_url": result.get("widget_url"),
            "transaction_type": result.get("transaction_type"),
        } if result.get("success") else None
        
        response_dto = WalletResponseDTO(
            data=response_data,
            message=result.get("message", "Transaction processed successfully"),
            success=result.get("success", False),
            status_code=status_code,
        )

        return wallet_system.api.create_response(
            request,
            response_dto,
            status=status_code
        )
        
    except Exception as ex:
        error_message = f"Failed to process MoonPay transaction: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )