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

sixth_description = """
Prepare and execute token swap
If private_key is provided, it will execute the swap using the appropriate web3 provider.
Otherwise, it will only prepare the transaction.

Returns:
    WalletResponseDTO containing:
    - data: Swap execution data (tx_hash for execute, quote data for prepare)
    - quote_data: Detailed quote information (when preparing)
    - message: Status message
    - success: Boolean indicating operation status
    - status_code: HTTP status code
"""

seventh_description = """
Process Paybis transaction (buy/sell) and return widget URL

Args:
    from_currency_or_crypto: Source currency/crypto code
    to_currency_or_crypto: Target currency/crypto code
    amount: Amount to exchange
    partner_user_id: Your system's user ID
    email: User email
    direction: 'from' or 'to' (default 'from')
    locale: Language locale (default 'en')

Returns:
    WalletResponseDTO containing:
    - widget_url: URL for the Paybis widget
    - transaction_type: 'buy' or 'sell'
    - request_id: The Paybis request ID
    Or error information if unsuccessful
"""

eight_description = """
Process Transak transaction (buy/sell) and return widget URL

Args:
    from_currency_or_crypto: Source currency/crypto code
    to_currency_or_crypto: Target currency/crypto code
    amount: Amount to exchange
    wallet_address: User's wallet address
    direction: 'from' or 'to' (default 'from')
    locale: Language locale (default 'en')
    user_data: Optional additional parameters

Returns:
    WalletResponseDTO containing:
    - widget_url: URL for the Transak widget
    - transaction_type: 'buy' or 'sell'
    Or error information if unsuccessful
"""

ninth_description = """
Process MoonPay transaction (buy/sell) and return widget URL

Args:
    from_currency_or_crypto: Source currency/crypto code
    to_currency_or_crypto: Target currency/crypto code
    amount: Amount to exchange
    wallet_address: User's wallet address
    direction: 'from' or 'to' (default 'from')
    locale: Language locale (default 'en')
    user_data: Optional additional parameters

Returns:
    WalletResponseDTO containing:
    - widget_url: URL for the MoonPay widget
    - transaction_type: 'buy' or 'sell'
    Or error information if unsuccessful
"""


