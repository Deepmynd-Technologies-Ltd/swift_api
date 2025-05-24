from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.message import Message
from solana.rpc.api import Client
import solders
import base58
from home.wallet_schema import SendTransactionDTO

def send_sol(req: SendTransactionDTO):
    try:
        client = Client("https://api.mainnet-beta.solana.com")
        
        private_key_bytes = None
        
        # First, try to decode as base58 (common Solana format for keypairs)
        try:
            print(f"Original private_key input: {req.private_key}")
            
            # Try base58 decode first
            private_key_bytes = base58.b58decode(req.private_key)
            print(f"Base58 decoded length: {len(private_key_bytes)}")
            print(f"Base58 decoded bytes (hex): {private_key_bytes.hex()}")
            
            if len(private_key_bytes) == 64:
                sender_keypair = Keypair.from_bytes(private_key_bytes)
            elif len(private_key_bytes) == 32:
                sender_keypair = Keypair.from_seed(private_key_bytes)
            else:
                # Print the problematic sequence here:
                print(f"Unexpected base58 decoded length: {len(private_key_bytes)}")
                print(f"Decoded bytes: {private_key_bytes}")
                raise ValueError(f"Invalid base58 key length: {len(private_key_bytes)} bytes")
        except Exception as base58_err:
            print(f"Base58 decode failed or invalid length: {base58_err}")
            # Try hex decode fallback
            try:
                private_key_bytes = bytes.fromhex(req.private_key)
                print(f"Hex decoded length: {len(private_key_bytes)}")
                print(f"Hex decoded bytes (hex): {private_key_bytes.hex()}")
                
                if len(private_key_bytes) == 64:
                    sender_keypair = Keypair.from_bytes(private_key_bytes)
                elif len(private_key_bytes) == 32:
                    sender_keypair = Keypair.from_seed(private_key_bytes)
                else:
                    print(f"Unexpected hex decoded length: {len(private_key_bytes)}")
                    print(f"Decoded bytes: {private_key_bytes}")
                    raise ValueError(f"Invalid hex key length: {len(private_key_bytes)} bytes")
            except Exception as hex_err:
                print(f"Hex decode failed: {hex_err}")
                raise ValueError("Invalid private key format - must be base58 or hex")



        
        # Verify that the derived public key matches the from_address
        derived_address = str(sender_keypair.pubkey())
        if derived_address != req.from_address:
            raise ValueError(f"Address mismatch. Derived: {derived_address}, Expected: {req.from_address}")
        
        # Get recent blockhash
        recent_blockhash = client.get_latest_blockhash().value.blockhash
        
        # Create transfer instruction
        print(f"Preparing to transfer {req.amount} SOL from {req.from_address} to {req.to_address}")
        transfer_ix = solders.system_program.transfer(
            solders.system_program.TransferParams(
                from_pubkey=Pubkey(req.from_address),
                to_pubkey=Pubkey(req.to_address),
                lamports=int(req.amount * 10**9), 
            )
        )
        
        # Build and sign transaction
        message = Message([transfer_ix])
        transaction = Transaction(
            message=message,
            recent_blockhash=recent_blockhash,
        )
        transaction.sign([sender_keypair])
        
        # Send transaction
        response = client.send_transaction(transaction)
        
        return {
            "success": True,
            "result": response.to_json(),
            "status_code": 200,
            "tx_hash": str(response.value)
        }
        
    except Exception as ex:
        return {
            "success": False,
            "error": str(ex),
            "status_code": 400
        }
