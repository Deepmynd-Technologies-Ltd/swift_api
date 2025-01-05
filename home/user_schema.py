from pydantic import BaseModel
from ninja import Schema

class UserRequest(Schema):
    fullname: str
    email: str
    password: str

class UserLoginRequest(Schema):
    email: str
    password: str

class UserLoginResponse(Schema):
    id: str
    fullname: str
    email: str

class UserResponse(Schema):
    id: str
    fullname: str
    email: str
    user_type: str  # Include user_type for completeness

class UpdateUserRequest(Schema):
    fullname: str = None
    email: str = None
    password: str = None

