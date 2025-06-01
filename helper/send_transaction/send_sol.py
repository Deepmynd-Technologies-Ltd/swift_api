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
        
        # Convert hex private key to bytes
        hex_private_key = req.private_key
        if len(hex_private_key) == 64:  # Raw hex without 0x prefix
            private_key_bytes = binascii.unhexlify(hex_private_key)
        elif hex_private_key.startswith("0x") and len(hex_private_key) == 66:  # With 0x prefix
            private_key_bytes = binascii.unhexlify(hex_private_key[2:])
        else:
            raise ValueError("Invalid private key format - expected 64-character hex string")
            
        # Create keypair from private key bytes (32 bytes)
        sender_keypair = Keypair.from_seed(private_key_bytes)  # Changed from from_bytes()
        
        # Debug output
        print("Sender address:", sender_keypair.pubkey())
        print("Private key length:", len(private_key_bytes))
        
        # Check balance
        balance = solana_client.get_balance(sender_keypair.pubkey()).value
        if balance < req.amount * 10**9:
            raise RuntimeError("Insufficient balance")
        
        # Build transaction
        txn = Transaction().add(
            transfer(
                TransferParams(
                    from_pubkey=sender_keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(req.to_address),
                    lamports=int(req.amount * 10**9)
                )
            )
        )
        
        # Sign and send
        txn.sign(sender_keypair)
        tx_hash = solana_client.send_transaction(txn).value
        print(f"Transaction sent: https://solscan.io/tx/{tx_hash}")
        return tx_hash
    except Exception as ex:
        raise RuntimeError(f"{ex}")