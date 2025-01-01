from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.keypair import Keypair
import solders

from home.wallet_schema import SendTransactionDTO

def send_sol(req:SendTransactionDTO):
    try:
        client = Client("https://api.mainnet-beta.solana.com")
        sender_keypair = Keypair.from_secret_key(req.private_key)

        if sender_keypair.public_key is not req.from_address:
            raise Exception("Invalid address")

        # Convert amount to lamports (1 SOL = 1e9 lamports)
        lamports = int(req.amount * 1e9)
        # Create transaction
        transaction = Transaction().add(
            solders.system_program.transfer(
                solders.system_program.TransferParams(
                    from_pubkey= req.from_address,
                    to_pubkey=Pubkey(req.to_address),
                    lamports=lamports,
                )
            )
        )
        # Sign and send transaction
        response = client.send_transaction(transaction, sender_keypair)
        return response["result"]
    except Exception as ex:
        raise str(ex)