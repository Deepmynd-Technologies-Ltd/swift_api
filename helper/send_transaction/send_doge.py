import blockcypher
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

def send_doge(req: SendTransactionDTO, coin_symbol="doge"):
    try:
        satoshi = int(req.amount * 100_000_000)  # 1 DOGE = 100,000,000 satoshis (like BTC)
        validate_coin(req.to_address, coin_symbol)
        
        tx_hash = blockcypher.simple_spend(
            from_privkey=req.private_key,
            to_address=req.to_address,
            to_satoshis=satoshi,
            coin_symbol=coin_symbol,
            api_key=settings.BLOCK_CYPHER
        )
        return tx_hash
    except Exception as ex:
        raise RuntimeError(f"{ex}")

def validate_coin(address, coin_symbol):
    try:
        blockcypher.get_address_overview(address=address, coin_symbol=coin_symbol)
        return True
    except:
        raise RuntimeError(f"Invalid {coin_symbol} address")