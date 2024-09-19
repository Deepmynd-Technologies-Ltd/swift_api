from authentication.models import User
from helper.utils import make_transaction_to_wallet
from wallet.models import Transaction
from .schemas import CreateTransactionDTO, ResponseDTO



def send_eth(user, req:CreateTransactionDTO)->ResponseDTO:
  try:
    req_user = User.objects.get(email=user)
    if req_user is None:
      return ResponseDTO(message="Unauthorized user", status=401, success = False)

    val, gas_fee  = make_transaction_to_wallet(
      key=req_user.wallets.private_key,
      recipient_address=req.recipient_address,
      from_address=req.from_address,
      amount=req.amount,
      )
    print(val.status)
    print(gas_fee)
    Transaction.objects.create(
      wallet = req_user.wallets,
      tx_hash=val,
      from_address=req.from_address,
      to_address = req.recipient_address,
      amount = req.amount,
      gas_fee= 200000.0,
      status= (lambda x: "sent" if x == 1 else "pending")(val.status)
    )
    return ResponseDTO(message="Transaction sent",status=200, data="")
  except Exception as ex:
    return ResponseDTO(message=str(ex), status=400, success=False)