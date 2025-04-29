from ninja import Schema
from typing import Generic, TypeVar, Dict, List, Optional, Union, Any
from enum import Enum
from datetime import datetime
from pydantic import Field


T = TypeVar("T")

class PhraseRequest(Schema):
    phrase: str

class UserRequest(Schema):
    userId: str
    walletPin: str
    
class SendTransactionDTO(Schema):
    private_key: str
    amount: float
    to_address: str
    from_address: str
    crypto_symbol: str = "btc"

class Symbols(str, Enum):
    BTC = "btc"
    ETH = "eth"
    SOL = "sol"
    TRON = "trx"
    DODGE = "doge"
    BNB = "bnb"
    USDT = "usdt"

class HTTPStatusCode(int, Enum):
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500

class WalletResponseDTO(Schema, Generic[T]):
    data: Optional[T] = None
    status_code: HTTPStatusCode = HTTPStatusCode.OK
    success: bool = True
    message: str = ""

class WalletInfoResponse(Schema):
    name: str
    address: str
    private_key: str
    balance: float
    symbols: Symbols
    price: float
    changes: float
    volume: float
    idName: str
    icon_url: str

class TransactionType(str, Enum):
    SENT = "sent"
    RECEIVED = "received"

class TransactionsInfo(Schema):
    hash: str
    transaction_type: TransactionType
    amount: float
    timestamp: str
    hashUrl: str

# Swap-related schemas
class SwapStepTransactionData(Schema):
    """Nested schema for transaction data to avoid using Dict[str, Any]"""
    to: Optional[str] = None
    value: Optional[str] = None
    data: Optional[str] = None
    gas: Optional[str] = None
    chain_id: Optional[int] = Field(None, alias="chainId")

class SwapStep(Schema):
    type: str = Field(..., description="Type of step (swap/bridge)")
    tool: str = Field(..., description="Tool used (1inch, 0x, Li.Fi, Rango)")
    description: str = Field(..., description="Human-readable description")
    transaction_data: SwapStepTransactionData = Field(
        ...,
        description="Structured transaction data"
    )

class SwapQuoteResponse(Schema):
    from_amount: str = Field(..., description="Amount to send")
    to_amount: str = Field(..., description="Expected amount to receive")
    estimated_gas: Optional[str] = Field(None, description="Estimated gas cost")
    slippage: float = Field(..., description="Applied slippage percentage")
    steps: List[SwapStep] = Field(..., description="List of swap steps")
    expiration: int = Field(..., description="Quote expiration timestamp")

class SwapRouteStep(Schema):
    """Schema for individual route steps"""
    service: str
    from_token: str = Field(..., alias="fromToken")
    to_token: str = Field(..., alias="toToken")
    from_amount: str = Field(..., alias="fromAmount")
    to_amount: str = Field(..., alias="toAmount")

class SwapExecuteRequest(Schema):
    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    amount: str
    user_address: str
    receiver_address: str
    route: Optional[List[SwapRouteStep]] = Field(
        None,
        description="The full route from quote"
    )

class SwapTransaction(Schema):
    """Schema for individual transactions in SwapExecuteResponse"""
    to: str
    value: str
    data: str
    gas: Optional[str] = None
    chain_id: Optional[int] = Field(None, alias="chainId")

class SwapExecuteResponse(Schema):
    transactions: List[SwapTransaction]
    signing_prompts: List[str]

class SwapStatusStep(Schema):
    """Schema for individual steps in SwapStatusResponse"""
    status: str
    description: str
    tx_hash: Optional[str] = Field(None, alias="txHash")

class SwapStatusResponse(Schema):
    status: str = Field(..., description="Overall swap status")
    steps: List[SwapStatusStep]
    explorer_links: List[str] = Field(
        ...,
        description="List of blockchain explorer links for each step"
    )

class HttpRequest(Schema):
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Union[str, int]]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = 30
    retries: Optional[int] = 3
    retry_delay: Optional[int] = 5

class HttpResponse(Schema):
    status_code: int
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SwapQuoteRequest(Schema):
    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    from_amount: str
    user_address: str
    receiver_address: Optional[str] = None
    slippage: Optional[float] = 0.5  # Default slippage percentage
    