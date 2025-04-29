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

Swap Flow:
1. Get quote (optional) - /swap_quote
2. Prepare transaction - /swap_wallet
3. User signs transaction in their wallet
4. Transaction broadcast to network

Request Parameters:
- to_symbol: Target cryptocurrency symbol
- amount: Amount to swap (in smallest unit)
- sender_address: Originating wallet address
- receiver_address: Destination address (optional, defaults to sender)
- slippage: Maximum acceptable slippage % (default: 0.5%)

Response Includes:
- Transaction data for signing
- Estimated gas fees (where applicable)
- Swap route details
- Status tracking information

Usage Example:
{
  "to_symbol": "USDT",
  "amount": "1000000000000000000", // 1 ETH in wei
  "sender_address": "0x123...",
  "receiver_address": "0x456...", // Optional
  "slippage": 0.5 // Optional
}

Response Example:
{
  "data": {
    "transaction_data": {
      "to": "0xcontract...",
      "value": "0",
      "data": "0xencoded...",
      "gas": "21000"
    },
    "swap_details": {
      "from_token": "ETH",
      "to_token": "USDT",
      "estimated_amount": "1500000000", // 1500 USDT
      "minimum_received": "1492500000" // After slippage
    }
  },
  "status_code": 200,
  "success": true,
  "message": "Transaction ready for signing"
}
"""