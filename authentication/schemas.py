from ninja.schema import BaseModel, Schema, Field
from typing import Any, Optional
from uuid import uuid4, UUID

class GoogleTokenDTO(BaseModel):
  token:str
  email:str
  name:str

class ResponseDTO(BaseModel):
  data: Any = None
  status:int = 200
  success:bool = True
  message:str

class UserResponse(Schema):
  id:UUID = Field(default_factory=uuid4)
  email: str
  fullname:str
  balance:float = None
  wallet_address:str = None
