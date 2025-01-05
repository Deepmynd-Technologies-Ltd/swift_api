from authentication.schemas import ResponseDTO, GoogleTokenDTO, UserResponse
from .models import User
from helper.utils import Google, create_jwt_token, generate_user_wallet_address, get_wallet_balance
from django.conf import settings
from decouple import config

def register_login(auth_token:GoogleTokenDTO)->ResponseDTO:
  """
  Register or login a user using google auth token
  """
  userData = Google.validate_token(auth_token=auth_token.token)
  if type(userData) is str:
    return ResponseDTO(message=userData, status=400, success=False)

  if userData["aud"] != config("GOOGLE_Client_ID"):
    return ResponseDTO(message="Invalid access token", success=False, status= 400)

  email = userData["email"]
  fullname=userData["name"]

  user, created = User.objects.get_or_create(email=email, defaults={
    "fullname":fullname,
    "password":settings.GOOGLE_PASSWORD,
  })
  if created:
    generate_user_wallet_address(user)
  token = create_jwt_token(user=user)

  return ResponseDTO(data=token, message="All good", status=200, success=True)

def testing_login()->ResponseDTO:
  user, created = User.objects.get_or_create(email="joseph@gmail.com", defaults={
    "fullname": "Joseph Oladele",
    "password": settings.GOOGLE_PASSWORD,
  })
  if created:
    generate_user_wallet_address(user=user)
  token = create_jwt_token(user=user)
  return ResponseDTO(data=token, status=200, message="All good", success=True)


def get_user_account(user):
    res = User.objects.get(email = user)
    if res is None:
        return ResponseDTO(message="Unauthorized User", status=401)
    val = UserResponse.from_orm(res)
    res.wallets.amount = get_wallet_balance(res.wallets.private_key)
    val.balance = round(res.wallets.amount, 2)
    val.wallet_address = res.wallets.address
    print(val)
    return ResponseDTO(message="Welcome back", success=True, status=200, data=val)