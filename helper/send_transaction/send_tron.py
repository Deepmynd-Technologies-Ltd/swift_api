from tronpy import Tron

from home.wallet_schema import SendTransactionDTO

def send_trx(req:SendTransactionDTO):
    client = Tron()
    sender = client.get_account(req.private_key)
    if sender is not req.from_address:
        raise Exception("Invalid address")

    txn = (
        client.trx.transfer(sender["address"], req.to_address, int(req.amount * 1e6))
        .build()
        .sign(req.private_key)
    )
    return txn.broadcast().get("txid")