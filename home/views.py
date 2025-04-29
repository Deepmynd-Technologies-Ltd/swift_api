# views.py
from typing import Dict, List, Optional
from ninja import Router
from authentication.models import User
from helper.api_documentation import first_description, second_description, third_description, fourth_description, fifth_description, swap_description
from helper.coingeko_api import get_coins_value
from home.wallet_schema import PhraseRequest, SendTransactionDTO, Symbols, TransactionsInfo, WalletInfoResponse, WalletResponseDTO, UserRequest, SwapStepTransactionData, SwapStep, SwapQuoteResponse, SwapQuoteRequest, SwapRouteStep, SwapExecuteRequest, SwapTransaction, SwapExecuteResponse, SwapStatusStep, SwapStatusResponse, HttpRequest, HTTPStatusCode
from home.wallet_services import generate_secrete_phrases, get_all_transactions_history, get_wallet_balance, import_from_phrases, send_crypto_transaction
from helper.utils import generate_user_wallet_address
import traceback

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

@wallet_system.post("swap_wallet/", response=WalletResponseDTO[str], description=fifth_description, summary="Swap Wallet")
def swap_wallet(request, symbol:Symbols, req:SendTransactionDTO):
  val = send_crypto_transaction(symbol, req)
  return wallet_system.api.create_response(request, val, status=val.status_code)

@wallet_system.post(
    "swap_wallet/", 
    response=WalletResponseDTO[Dict],
    description=swap_description,
    summary="Execute Token Swap"
)
def swap_wallet(request: HttpRequest, symbol: Symbols, req: SendTransactionDTO):
    """
    Execute a token swap between supported assets.
    
    Supports both intra-chain and cross-chain swaps.
    Returns transaction data that needs to be signed by the user's wallet.
    """
    try:
        # Validate the token pair
        from_config = CHAIN_CONFIG.get(symbol)
        to_config = CHAIN_CONFIG.get(req.to_symbol)
        
        if not from_config or not to_config:
            return wallet_system.api.create_response(
                request,
                WalletResponseDTO(
                    message="Unsupported token pair",
                    success=False,
                    status_code=HTTPStatusCode.BAD_REQUEST
                ),
                status=HTTPStatusCode.BAD_REQUEST
            )

        # Execute the swap
        result = swap_crypto_transaction(symbol, req)
        
        # Format the response
        response_data = {
            "transaction_data": result.data if result.success else None,
            "signing_instructions": "Please sign this transaction in your wallet",
            "estimated_gas": None,  # Would be populated in real implementation
            "swap_details": {
                "from_token": symbol.name,
                "to_token": req.to_symbol.name,
                "amount": req.amount
            }
        }
        
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data=response_data,
                message=result.message,
                success=result.success,
                status_code=result.status_code or HTTPStatusCode.OK
            ),
            status=result.status_code or HTTPStatusCode.OK
        )

    except Exception as ex:
        error_message = f"Swap failed: {str(ex)}"
        traceback.print_exc()
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR
            ),
            status=HTTPStatusCode.INTERNAL_SERVER_ERROR
        )

@wallet_system.get(
    "swap_quote/",
    response=WalletResponseDTO[Dict],
    summary="Get Swap Quote"
)
def get_swap_quote(request: HttpRequest, params: SwapQuoteRequest):
    """
    Get a quote for a potential token swap.
    Includes estimated amounts, fees, and slippage information.
    """
    try:
        provider = get_swap_provider(params.from_chain, params.to_chain)
        quote = get_swap_quote(provider, params.dict())
        
        if not quote:
            raise ValueError("Failed to get swap quote from provider")
        
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data=quote,
                message="Swap quote retrieved successfully",
                success=True
            ),
            status=HTTPStatusCode.OK
        )
        
    except Exception as ex:
        error_message = f"Quote failed: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            ),
            status=HTTPStatusCode.BAD_REQUEST
        )

@wallet_system.post(
    "execute_swap/",
    response=WalletResponseDTO[Dict],
    summary="Execute Prepared Swap"
)
def execute_swap(request: HttpRequest, payload: SwapExecuteRequest):
    """
    Execute a previously quoted swap.
    Requires the user to have approved the transaction.
    """
    try:
        # In a real implementation, you would verify the quote and prepare the final transaction
        # This is a simplified version that just returns the transaction data
        
        transaction_data = {
            "to": payload.receiver_address,
            "value": str(payload.amount),
            "data": "0x",  # Would be actual call data in implementation
            "chainId": CHAIN_IDS.get(payload.from_chain, 1)
        }
        
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                data={"transactions": [transaction_data]},
                message="Transaction prepared. Please sign in your wallet.",
                success=True
            ),
            status=HTTPStatusCode.OK
        )
        
    except Exception as ex:
        error_message = f"Execution failed: {str(ex)}"
        return wallet_system.api.create_response(
            request,
            WalletResponseDTO(
                message=error_message,
                success=False,
                status_code=HTTPStatusCode.BAD_REQUEST
            ),
            status=HTTPStatusCode.BAD_REQUEST
        )

