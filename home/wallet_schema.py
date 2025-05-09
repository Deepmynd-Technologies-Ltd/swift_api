from ninja import Schema
from typing import Generic, TypeVar, Dict, List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from django.http import HttpRequest


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
  data: T = None
  status_code:HTTPStatusCode = HTTPStatusCode.OK
  success:bool = True
  message:str

class WalletInfoResponse(Schema):
  name:str
  address:str
  private_key: str
  balance:float
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
  hash:str
  transaction_type: TransactionType
  amount: float
  timestamp: str
  hashUrl:str

# Swap schemas

class SwapProvider(str, Enum):
    PAYBIS = "paybis"
    KOTANIPAY = "kotanipay"
    TRANSAK = "transak"

class SwapStepTransactionData(BaseModel):
    data: str
    to: str
    value: str
    from_address: Optional[str] = Field(None, alias="from")
    gas_limit: Optional[str] = None

class SwapStep(BaseModel):
    type: str
    tool: str
    action: Dict[str, Any]
    estimate: Optional[Dict[str, Any]] = None
    transaction_data: Optional[SwapStepTransactionData] = None

class SwapQuoteRequest(BaseModel):
    from_symbol: Symbols
    to_symbol: Symbols
    amount: Union[str, float, Decimal]
    from_address: str
    to_address: Optional[str] = None
    slippage: Optional[float] = 0.5
    provider: Optional[SwapProvider] = None

class SwapRouteStep(BaseModel):
    type: str
    tool: str
    tool_details: Optional[Dict[str, Any]] = None
    action: Dict[str, Any]
    estimate: Optional[Dict[str, Any]] = None

class SwapQuoteResponse(BaseModel):
    quote_id: str
    from_token: Dict[str, Any]
    to_token: Dict[str, Any]
    steps: List[SwapRouteStep]
    fee: Optional[str] = None
    gas_estimate: Optional[str] = None
    provider: str
    expiry: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None

class SwapExecuteRequest(BaseModel):
    quote_id: str
    from_address: str
    to_address: Optional[str] = None
    signature: Optional[str] = None
    provider: Optional[SwapProvider] = None
    # The following fields would normally be retrieved from the database
    # but are included here to simplify testing with Postman
    from_symbol: Optional[Symbols] = None
    to_symbol: Optional[Symbols] = None
    from_token_address: Optional[str] = None
    to_token_address: Optional[str] = None
    amount: Optional[Union[str, float, Decimal]] = None
    slippage: Optional[float] = None

class SwapTransaction(BaseModel):
    from_address: str
    to_address: str
    data: str
    value: str
    chain_id: Union[int, str]
    gas_limit: Optional[str] = None
    gas_price: Optional[str] = None

class SwapExecuteResponse(BaseModel):
    transaction: SwapTransaction
    estimated_output: str
    provider: str
    steps: Optional[List[Dict[str, Any]]] = None

class SwapStatusStep(BaseModel):
    type: str
    status: str
    tx_hash: Optional[str] = None
    chain: str
    tool: str
    error: Optional[str] = None

class SwapStatusResponse(BaseModel):
    status: str
    steps: List[SwapStatusStep]
    from_token: Dict[str, Any]
    to_token: Dict[str, Any]
    estimated_received: Optional[str] = None
    actual_received: Optional[str] = None
