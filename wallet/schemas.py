from ninja.schema import Schema, BaseModel
from typing import Any

class CreateTransactionDTO(Schema):
  recipient_address: str
  from_address: str
  amount:float
  token: str = "Eth"


class ResponseDTO(BaseModel):
  data: Any = None
  status:int = 200
  success:bool = True
  message:str