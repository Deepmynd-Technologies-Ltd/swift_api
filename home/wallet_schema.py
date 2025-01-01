from ninja import Schema
from typing import Generic, TypeVar
from enum import Enum

T = TypeVar("T")

class PhraseRequest(Schema):
  phrase: str

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