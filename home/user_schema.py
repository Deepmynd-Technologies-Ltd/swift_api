from pydantic import BaseModel
from ninja import Schema

class UserRequest(Schema):
    fullname: str
    email: str
    password: str

class UserResponse(Schema):
    id: str
    fullname: str
    email: str
    user_type: str  # Include user_type for completeness

class UpdateUserRequest(Schema):
    fullname: str = None
    email: str = None
    password: str = None
