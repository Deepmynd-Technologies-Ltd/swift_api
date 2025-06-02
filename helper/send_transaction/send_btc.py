import blockcypher
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

def send_btc(req: SendTransactionDTO, coin_symbol="btc"):
    try:
        # Convert BTC to satoshis
        satoshi = int(req.amount * 100_000_000)

        # Validate recipient address
        validate_coin(req.to_address, coin_symbol)

        # Send the transaction
        tx_hash = blockcypher.simple_spend(
            from_privkey=req.private_key,
            to_address=req.to_address,
            to_satoshis=satoshi,
            coin_symbol=coin_symbol,
            api_key=settings.BLOCK_CYPHER
        )

        # Fetch transaction details for confirmation
        tx_details = blockcypher.get_transaction_details(
            tx_hash, 
            coin_symbol=coin_symbol,
            api_key=settings.BLOCK_CYPHER
        )

        # Optional: Log or return tx_details if needed
        return tx_hash

    except Exception as ex:
        raise RuntimeError(f"BTC transfer failed: {ex}")

def validate_coin(address, coin_symbol):
    try:
        blockcypher.get_address_overview(address=address, coin_symbol=coin_symbol)
        return True
    except Exception as e:
        raise ValueError(f"Invalid {coin_symbol} address: {e}")
