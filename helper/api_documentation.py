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

swap_description = """
Executes a token swap between supported assets, handling both intra-chain and cross-chain swaps.

Features:
- Supports BNB (BEP20), BTC, DOGE, ETH, SOL, and USDT (BEP20)
- Automatic routing through best available liquidity providers
- Slippage tolerance configuration
- Returns transaction data for wallet signing (never handles private keys)
"""

buy_crypto_description = """
Allows users to purchase cryptocurrencies using credit/debit cards or bank transfers.
Supported Cryptocurrencies:
- BTC, DOGE, BNB, ETH, SOL, USDT (BEP20/ERC20)
- Provides a seamless experience for users to acquire crypto assets
- Integrates with third-party payment processors for secure transactions
"""

sell_crypto_description = """
Allows users to sell cryptocurrencies for fiat currency.
Supported Cryptocurrencies:
- BTC, DOGE, BNB, ETH, SOL, USDT (BEP20/ERC20)
- Provides a seamless experience for users to convert crypto assets to fiat
- Integrates with third-party payment processors for secure transactions
"""

payment_methods_description = """
Fetches available payment methods for buying/selling cryptocurrencies.
- Supports various fiat currencies and payment options
- Integrates with third-party payment processors for secure transactions
- Provides users with a list of available payment options based on their location
"""

currencies_description = """
Fetches the list of supported cryptocurrencies for trading.
- Provides detailed information about each cryptocurrency
- Integrates with third-party exchanges for real-time data
- Ensures users have access to the latest information about supported assets
"""



