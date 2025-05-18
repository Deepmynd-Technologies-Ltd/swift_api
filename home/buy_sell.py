from typing import Dict, Optional
import requests
from decimal import Decimal
from django.conf import settings
from home.wallet_schema import HTTPStatusCode

# Define fiat and crypto sets for quick membership checking
FIAT_CURRENCIES = {'NGN', 'EUR', 'USD', 'GBP'}
CRYPTO_CURRENCIES = {'BNB', 'BTC', 'ETH', 'USDT', 'DOGE', 'SOL'}

PAYBIS_CRYPTO_CURRENCY_MAP = {
    'BNB': 'BNBSC-TESTNET',
    'BTC': 'BTC-TESTNET',
    'ETH': 'ETH-SEPOLIA',
    'USDT': 'USDT-TRC20-SHASTA',
    'DOGE': 'DOGE',
    'SOL': 'SOL',
    'NGN': 'NGN',
    'EUR': 'EUR',
    'USD': 'USD',
    'GBP': 'GBP'
}

TRANSAK_CRYPTO_NETWORK_MAP = {
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancesmartchain',
    'BTC': 'bitcoin',
    'DOGE': 'dogecoin',
    'USDT': 'ethereum',
}

MOONPAY_CRYPTO_CURRENCY_MAP = {
    'ETH': 'eth',
    'SOL': 'sol',
    'BNB': 'bnb',
    'BTC': 'btc',
    'DOGE': 'doge',
    'USDT': 'usdt',
}

def process_paybis_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    partner_user_id: str,
    email: str,
    direction: str = 'from',
    locale: str = 'en'
) -> Dict:
    """
    Unified function to handle Paybis transactions (buy/sell) and return widget URL
    
    Args:
        from_currency_or_crypto: Source currency/crypto code
        to_currency_or_crypto: Target currency/crypto code
        amount: Amount to exchange
        partner_user_id: Your system's user ID
        email: User email
        direction: 'from' or 'to' (default 'from')
        locale: Language locale (default 'en')
    
    Returns:
        Dict containing:
        - success: bool indicating operation status
        - widget_url: URL for the Paybis widget
        - transaction_type: 'buy' or 'sell'
        - message: Status message
        - status_code: HTTP status code
    """
    # Convert currencies to uppercase
    from_curr = from_currency_or_crypto.upper()
    to_curr = to_currency_or_crypto.upper()

    # Validate direction
    if direction not in ['from', 'to']:
        return {
            'success': False,
            'message': "Direction must be either 'from' or 'to'",
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    # Validate currency support
    if from_curr not in PAYBIS_CRYPTO_CURRENCY_MAP or to_curr not in PAYBIS_CRYPTO_CURRENCY_MAP:
        return {
            'success': False,
            'message': 'Unsupported cryptocurrency or fiat',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    # Determine transaction type
    if to_curr in CRYPTO_CURRENCIES:
        transaction_type = 'buy'
    elif to_curr in FIAT_CURRENCIES:
        transaction_type = 'sell'
    else:
        return {
            'success': False,
            'message': 'Currency not recognized as fiat or crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    # Validate transaction constraints
    if transaction_type == 'sell' and from_curr not in CRYPTO_CURRENCIES:
        return {
            'success': False,
            'message': 'Selling requires crypto as from_currency',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    if transaction_type == 'buy' and from_curr not in FIAT_CURRENCIES:
        return {
            'success': False,
            'message': 'Buying requires fiat as from_currency',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    try:
        # Step 1: Get quote from Paybis
        quote_payload = {
            'currencyCodeFrom': PAYBIS_CRYPTO_CURRENCY_MAP[from_curr],
            'currencyCodeTo': PAYBIS_CRYPTO_CURRENCY_MAP[to_curr],
            'amount': str(amount),
            'directionChange': direction,
            'isReceivedAmount': False
        }

        headers = {
            'Authorization': settings.PAYBIS_API_KEY,
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        quote_response = requests.post(
            'https://widget-api.sandbox.paybis.com/v2/quote',
            headers=headers,
            json=quote_payload
        )

        if quote_response.status_code != 200:
            error_data = quote_response.json()
            error_msg = "Unknown Paybis error"
            if 'paymentMethodErrors' in error_data:
                error_msg = error_data['paymentMethodErrors'][0]['error']['message']
            elif 'payoutMethodErrors' in error_data:
                error_msg = error_data['payoutMethodErrors'][0]['error']['message']
            
            return {
                'success': False,
                'message': f"Paybis quote error: {error_msg}",
                'status_code': quote_response.status_code
            }

        quote_data = quote_response.json()
        quote_id = quote_data.get('id')

        # Step 2: Create transaction request
        request_payload = {
            'quoteId': quote_id,
            'partnerUserId': partner_user_id,
            'locale': locale,
            'email': email
        }

        request_response = requests.post(
            'https://widget-api.sandbox.paybis.com/v2/request',
            headers=headers,
            json=request_payload
        )

        if request_response.status_code != 200:
            return {
                'success': False,
                'message': f"Paybis request API error: {request_response.status_code}",
                'status_code': request_response.status_code,
                'details': request_response.json()
            }

        request_data = request_response.json()
        request_id = request_data.get('requestId')

        # Step 3: Construct appropriate widget URL based on transaction type
        if transaction_type == 'buy':
            widget_url = f"https://widget.sandbox.paybis.com/?requestId={request_id}&apiKey={settings.PAYBIS_API_KEY}#/v2/exchange-form"
        else:  # sell
            widget_url = f"https://widget-api.sandbox.paybis.com/v1/request/{request_id}?Authorization={settings.PAYBIS_API_KEY}&accept=application/json"

        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': transaction_type,
            'message': "Transaction processed successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'request_id': request_id,
            'quote_response': quote_data,
        }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f"Network error communicating with Paybis: {str(e)}",
            'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Unexpected error processing Paybis transaction: {str(e)}",
            'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR
        }

def process_transak_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None
) -> Dict:
    """
    Process Transak transaction (buy/sell) and return widget URL
    
    Args:
        from_currency_or_crypto: Source currency/crypto code
        to_currency_or_crypto: Target currency/crypto code
        amount: Amount to exchange
        wallet_address: User's wallet address for crypto transactions
        direction: 'from' (amount is in source currency) or 'to' (amount is in target currency)
        locale: Language/locale code
        user_data: Optional additional user data
    
    Returns:
        Dict containing:
        - success: bool
        - widget_url: str
        - transaction_type: 'buy' or 'sell'
        - message: str
        - status_code: int
    """
    # Convert to uppercase
    from_curr = from_currency_or_crypto.upper()
    to_curr = to_currency_or_crypto.upper()

    # Determine transaction type
    if to_curr in CRYPTO_CURRENCIES:
        transaction_type = 'buy'
    elif to_curr in FIAT_CURRENCIES:
        transaction_type = 'sell'
    else:
        return {
            'success': False,
            'message': 'Currency not recognized as fiat or crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    # Validate currencies
    if transaction_type == 'buy':
        if from_curr not in FIAT_CURRENCIES or to_curr not in CRYPTO_CURRENCIES:
            return {
                'success': False,
                'message': 'Buy transactions require fiat to crypto',
                'status_code': HTTPStatusCode.BAD_REQUEST
            }
    else:  # sell
        if from_curr not in CRYPTO_CURRENCIES or to_curr not in FIAT_CURRENCIES:
            return {
                'success': False,
                'message': 'Sell transactions require crypto to fiat',
                'status_code': HTTPStatusCode.BAD_REQUEST
            }

    try:
        base_url = "https://global-stg.transak.com" if settings.TRANSAK_SANDBOX else "https://global.transak.com"
        
        if transaction_type == 'buy':
            widget_url = (
                f"{base_url}?apiKey={settings.TRANSAK_API_KEY}"
                f"&productsAvailed=BUY"
                f"&walletAddress={wallet_address}"
                f"&cryptoCurrency={to_curr}"
                f"&fiatCurrency={from_curr}"
                f"&network={TRANSAK_CRYPTO_NETWORK_MAP.get(to_curr, 'ethereum')}"
                f"&defaultCryptoAmount={amount if direction == 'to' else ''}"
                f"&defaultFiatAmount={amount if direction == 'from' else ''}"
            )
        else:  # sell
            widget_url = (
                f"{base_url}?apiKey={settings.TRANSAK_API_KEY}"
                f"&productsAvailed=SELL"
                f"&walletAddress={wallet_address}"
                f"&cryptoCurrency={from_curr}"
                f"&fiatCurrency={to_curr}"
                f"&network={TRANSAK_CRYPTO_NETWORK_MAP.get(from_curr, 'ethereum')}"
                f"&defaultCryptoAmount={amount if direction == 'from' else ''}"
                f"&defaultFiatAmount={amount if direction == 'to' else ''}"
            )

        # Add optional user data if provided
        if user_data:
            for key, value in user_data.items():
                widget_url += f"&{key}={value}"

        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': transaction_type,
            'message': "Transak widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Error generating Transak widget: {str(e)}",
            'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR
        }

def process_moonpay_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None
) -> Dict:
    """
    Process MoonPay transaction (buy/sell) and return widget URL
    
    Args:
        from_currency_or_crypto: Source currency/crypto code
        to_currency_or_crypto: Target currency/crypto code
        amount: Amount to exchange
        wallet_address: User's wallet address for crypto transactions
        direction: 'from' (amount is in source currency) or 'to' (amount is in target currency)
        locale: Language/locale code
        user_data: Optional additional user data
    
    Returns:
        Dict containing:
        - success: bool
        - widget_url: str
        - transaction_type: 'buy' or 'sell'
        - message: str
        - status_code: int
    """
    # Convert to uppercase
    from_curr = from_currency_or_crypto.upper()
    to_curr = to_currency_or_crypto.upper()

    # Determine transaction type
    if to_curr in CRYPTO_CURRENCIES:
        transaction_type = 'buy'
    elif to_curr in FIAT_CURRENCIES:
        transaction_type = 'sell'
    else:
        return {
            'success': False,
            'message': 'Currency not recognized as fiat or crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }

    # Validate currencies
    if transaction_type == 'buy':
        if from_curr not in FIAT_CURRENCIES or to_curr not in CRYPTO_CURRENCIES:
            return {
                'success': False,
                'message': 'Buy transactions require fiat to crypto',
                'status_code': HTTPStatusCode.BAD_REQUEST
            }
    else:  # sell
        if from_curr not in CRYPTO_CURRENCIES or to_curr not in FIAT_CURRENCIES:
            return {
                'success': False,
                'message': 'Sell transactions require crypto to fiat',
                'status_code': HTTPStatusCode.BAD_REQUEST
            }

    try:
        if transaction_type == 'buy':
            base_url = "https://buy-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://buy.moonpay.com"
            widget_url = (
                f"{base_url}/?apiKey={settings.MOONPAY_API_KEY}"
                f"&walletAddress={wallet_address}"
                f"&currencyCode={MOONPAY_CRYPTO_CURRENCY_MAP.get(to_curr, to_curr.lower())}"
                f"&baseCurrencyCode={from_curr}"
                f"&baseCurrencyAmount={amount if direction == 'from' else ''}"
                f"&currencyAmount={amount if direction == 'to' else ''}"
            )
        else:  # sell
            base_url = "https://sell-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://sell.moonpay.com"
            widget_url = (
                f"{base_url}/?apiKey={settings.MOONPAY_API_KEY}"
                f"&walletAddress={wallet_address}"
                f"&currencyCode={MOONPAY_CRYPTO_CURRENCY_MAP.get(from_curr, from_curr.lower())}"
                f"&baseCurrencyCode={to_curr}"
                f"&baseCurrencyAmount={amount if direction == 'to' else ''}"
                f"&currencyAmount={amount if direction == 'from' else ''}"
            )

        # Add optional parameters
        if locale:
            widget_url += f"&language={locale}"
        
        if user_data:
            for key, value in user_data.items():
                widget_url += f"&{key}={value}"

        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': transaction_type,
            'message': "MoonPay widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS
        }

    except Exception as e:
        return {
            'success': False,
            'message': f"Error generating MoonPay widget: {str(e)}",
            'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR
        }

