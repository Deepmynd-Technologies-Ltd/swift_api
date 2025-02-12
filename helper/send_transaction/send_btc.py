import blockcypher
from django.conf import settings
from home.wallet_schema import SendTransactionDTO

def send_btc(req: SendTransactionDTO, coin_symbol="btc"):
  try:
    satoshi = int(req.amount * 100_000_000)  # Convert BTC amount to satoshis
    validate_coin(req.to_address, coin_symbol)  # Validate the address
    tx_hash = blockcypher.simple_spend(
        from_privkey=req.private_key,
        to_address=req.to_address,
        to_satoshis=satoshi,
        coin_symbol=coin_symbol,
        api_key=settings.BLOCK_CYPHER
    )
    tx_details = blockcypher.get_transaction_details(tx_hash, coin_symbol="btc", api_key=settings.BLOCK_CYPHER)
    print(tx_details)
    return tx_hash  # Return the transaction hash
  except Exception as e:
    print(f"Error in send_btc: {str(e)}")
    raise e  # Reraise the exception for further handling

def validate_coin(address, coin_symbol):
  try:
    blockcypher.get_address_overview(address=address, coin_symbol=coin_symbol)
    return True
  except:
    raise f"Invalid {coin_symbol} address"