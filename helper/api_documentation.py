# API Descriptions

first_description = """
Generates a secure 12/24-word mnemonic phrase that can be imported into any supported wallet application.
This phrase adheres to BIP-39 standards and ensures compatibility across wallets.

Usage Example:
{
  "phrase": "abandon ability able about above absent absorb abstract absurd abuse access accident"
}
"""

second_description = """
Generates wallet addresses for the following cryptocurrencies based on the provided mnemonic phrase:
- BTC (SegWit)
- DOGE
- BNB
- ETH
- SOL
- TRON
- USDT BEP-20

This endpoint ensures deterministic wallet generation for seamless integration with external platforms.

Usage Example:
{
  "wallets": {
    "BTC": "bc1qxyz...",
    "DOGE": "DHxy...",
    "BNB": "bnb1xyz...",
    "ETH": "0xabc...",
    "SOL": "ABC123...",
    "TRON": "Txyz...",
    "USDT": "0xabc..." // BEP-20
  }
}
"""

third_description = """
Fetches the current balance of the provided wallet address for the specified cryptocurrency.

Limitations:
- This endpoint has usage restrictions on the number of times it can be called due to API rate limits from blockchain providers.

Usage Example:
{
  "data": 0,
  "status_code": 200,
  "success": true,
  "message": "string"
}
"""

fourth_description = """
Fetches the transaction history for the provided wallet address and cryptocurrency symbol.
Each transaction includes an identifier to distinguish between received and sent transactions.

Transaction DTO Example:
{
  "data": [
    {
      "hash": "string",
      "transaction_type": "sent",
      "amount": 0,
      "timestamp": "string"
    }
  ],
  "status_code": 200,
  "success": true,
  "message": "string"
}
"""

fifth_description = """
Broadcasts a transaction to the blockchain network.
This endpoint handles the signing and submission of the transaction.

Supported Cryptocurrencies:
- BTC, DOGE, BNB, ETH, SOL, TRON, USDT (BEP-20/ERC-20)

Usage Example:
{
  "data": "string",
  "status_code": 200,
  "success": true,
  "message": "string"
}
"""