from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solana.rpc.api import Client
from solders.transaction import Transaction
import binascii
from home.wallet_schema import SendTransactionDTO

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

def send_sol(req: SendTransactionDTO):
    try:
        solana_client = Client(SOLANA_RPC_URL)

        # Decode private key (64-byte Solana secret key expected)
        hex_private_key = req.private_key
        if hex_private_key.startswith("0x"):
            hex_private_key = hex_private_key[2:]
        private_key_bytes = binascii.unhexlify(hex_private_key)

        if len(private_key_bytes) != 64:
            raise ValueError("Expected 64-byte Solana secret key (128 hex characters)")

        sender_keypair = Keypair.from_bytes(private_key_bytes)
        sender_pubkey = sender_keypair.pubkey()

        # Check balance in lamports (1 SOL = 1e9 lamports)
        balance = solana_client.get_balance(sender_pubkey).value
        required = int(req.amount * 10**9)
        if balance < required:
            raise RuntimeError("Insufficient balance")

        # Build and sign transaction
        recent_blockhash = solana_client.get_latest_blockhash().value.blockhash
        txn = Transaction(recent_blockhash=recent_blockhash).add(
            transfer(
                TransferParams(
                    from_pubkey=sender_pubkey,
                    to_pubkey=Pubkey.from_string(req.to_address),
                    lamports=required
                )
            )
        )

        # Send transaction
        tx_hash = solana_client.send_transaction(txn, sender_keypair).value
        return {
            "tx_hash": tx_hash,
            "explorer": f"https://solscan.io/tx/{tx_hash}"
        }

    except Exception as ex:
        raise RuntimeError(f"SOL transfer failed: {ex}")
