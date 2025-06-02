import blockcypher
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

def send_doge(req: SendTransactionDTO, coin_symbol="doge"):
    try:
        # Convert DOGE to satoshis
        satoshi = int(req.amount * 100_000_000)

        # Validate recipient address
        validate_coin(req.to_address, coin_symbol)

        # Optional: Validate sender's address matches private key
        pubkey = blockcypher.get_pubkey_from_privkey(req.private_key, coin_symbol=coin_symbol)
        derived_address = blockcypher.pubkey_to_address(pubkey, coin_symbol=coin_symbol)
        if derived_address != req.from_address:
            raise ValueError("Private key does not match from_address")

        # Send DOGE
        tx_hash = blockcypher.simple_spend(
            from_privkey=req.private_key,
            to_address=req.to_address,
            to_satoshis=satoshi,
            coin_symbol=coin_symbol,
            api_key=settings.BLOCK_CYPHER
        )

        # Optional: could log or return details
        # tx_details = blockcypher.get_transaction_details(tx_hash, coin_symbol=coin_symbol, api_key=settings.BLOCK_CYPHER)
        return tx_hash

    except Exception as ex:
        raise RuntimeError(f"DOGE transfer failed: {ex}")

def validate_coin(address, coin_symbol):
    try:
        blockcypher.get_address_overview(address=address, coin_symbol=coin_symbol)
        return True
    except Exception as e:
        raise ValueError(f"Invalid {coin_symbol} address: {e}")
