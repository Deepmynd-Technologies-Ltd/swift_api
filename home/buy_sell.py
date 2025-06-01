from typing import Dict, Optional
import requests
from decimal import Decimal
from django.conf import settings
from home.wallet_schema import HTTPStatusCode

# Constants
FIAT_CURRENCIES = {'NGN', 'EUR', 'USD', 'GBP'}
CRYPTO_CURRENCIES = {'BNB', 'BTC', 'ETH', 'USDT', 'DOGE', 'SOL'}

PROVIDER_CURRENCY_MAPS = {
    'PAYBIS': {'BNB': 'BNBSC-TESTNET', 'BTC': 'BTC-TESTNET','ETH': 'ETH-SEPOLIA','USDT': 'USDT-TRC20-SHASTA','DOGE': 'DOGE','SOL': 'SOL','NGN': 'NGN','EUR': 'EUR','USD': 'USD','GBP': 'GBP'},
    'TRANSAK': {'ETH': 'ethereum','SOL': 'solana', 'BNB': 'binancesmartchain','BTC': 'bitcoin','DOGE': 'dogecoin','USDT': 'ethereum'},
    'MOONPAY': {'ETH': 'eth','SOL': 'sol','BNB': 'bnb','BTC': 'btc','DOGE': 'doge','USDT': 'usdt'}
}

# Monetization configuration for buy/sell
BUY_SELL_MONETIZATION = {
    'base_fee_percent': Decimal('0.01'),  # 1% base fee
    'transaction_fee': {
        'buy': Decimal('0.005'),  # 0.5% for buys
        'sell': Decimal('0.007')  # 0.7% for sells
    },
    'min_fee': {
        'USD': Decimal('0.50'),
        'EUR': Decimal('0.45'),
        'GBP': Decimal('0.40'),
        'NGN': Decimal('200'),
    },
    'settlement_wallets': {
        'BTC': settings.BTC_FEE_WALLET if hasattr(settings, 'BTC_FEE_WALLET') else 'your_btc_wallet',
        'ETH': settings.ETH_FEE_WALLET if hasattr(settings, 'ETH_FEE_WALLET') else 'your_eth_wallet',
        'USDT': settings.USDT_FEE_WALLET if hasattr(settings, 'USDT_FEE_WALLET') else 'your_usdt_wallet',
    }
}

def calculate_buy_sell_fee(amount: Decimal, currency: str, transaction_type: str) -> Dict:
    """Calculate fees for buy/sell transactions."""
    currency = currency.upper()
    config = BUY_SELL_MONETIZATION
    
    # Calculate base fee
    base_fee = amount * config['base_fee_percent']
    
    # Calculate transaction fee
    tx_fee = amount * config['transaction_fee'].get(transaction_type, Decimal('0'))
    
    # Calculate total fee with minimum
    total_fee = base_fee + tx_fee
    min_fee = config['min_fee'].get(currency, Decimal('0'))
    final_fee = max(total_fee, min_fee)
    
    return {
        'gross_amount': amount,
        'net_amount': amount - final_fee,
        'fee_amount': final_fee,
        'fee_breakdown': {
            'base_fee': base_fee,
            'transaction_fee': tx_fee,
            'min_fee_applied': final_fee == min_fee
        },
        'currency': currency,
        'transaction_type': transaction_type
    }

def get_network_for_crypto(crypto_code: str) -> str:
    """Map cryptocurrency codes to their network names."""
    return PROVIDER_CURRENCY_MAPS['TRANSAK'].get(crypto_code.upper(), 'ethereum')

def _validate_transaction_currencies(from_curr: str, to_curr: str, provider: str) -> Optional[Dict]:
    """Validate currency support for transaction."""
    if from_curr not in PROVIDER_CURRENCY_MAPS[provider] or to_curr not in PROVIDER_CURRENCY_MAPS[provider]:
        return {
            'success': False,
            'message': 'Unsupported cryptocurrency or fiat',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    return None

def _determine_transaction_type(to_curr: str) -> Optional[Dict]:
    """Determine if transaction is buy or sell."""
    if to_curr in CRYPTO_CURRENCIES:
        return {'type': 'buy', 'error': None}
    elif to_curr in FIAT_CURRENCIES:
        return {'type': 'sell', 'error': None}
    return {
        'type': None,
        'error': {
            'success': False,
            'message': 'Currency not recognized as fiat or crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    }

def _validate_transaction_direction(transaction_type: str, from_curr: str) -> Optional[Dict]:
    """Validate transaction direction constraints."""
    if transaction_type == 'sell' and from_curr not in CRYPTO_CURRENCIES:
        return {
            'success': False,
            'message': 'Selling requires crypto as from_currency_or_crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    if transaction_type == 'buy' and from_curr not in FIAT_CURRENCIES:
        return {
            'success': False,
            'message': 'Buying requires fiat as from_currency_or_crypto',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    return None

def _process_monetization(amount: Decimal, currency: str, transaction_type: str) -> Dict:
    """Apply monetization fees to transaction amount."""
    fee_details = calculate_buy_sell_fee(amount, currency, transaction_type)
    return {
        'effective_amount': fee_details['net_amount'],
        'fee_details': fee_details
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
    """Handle Paybis transactions with monetization."""
    from_curr, to_curr = from_currency_or_crypto.upper(), to_currency_or_crypto.upper()
    
    # Validations
    if direction not in ['from', 'to']:
        return {'success': False, 'message': "Direction must be 'from' or 'to'", 'status_code': HTTPStatusCode.BAD_REQUEST}
    
    if error := _validate_transaction_currencies(from_curr, to_curr, 'PAYBIS'):
        return error
    
    trans_type = _determine_transaction_type(to_curr)
    if trans_type['error']:
        return trans_type['error']
    
    if error := _validate_transaction_direction(trans_type['type'], from_curr):
        return error
    
    try:
        # Apply monetization
        monetization = _process_monetization(
            amount, 
            from_curr if direction == 'from' else to_curr,
            trans_type['type']
        )
        
        # Get quote
        quote_payload = {
            'currencyCodeFrom': PROVIDER_CURRENCY_MAPS['PAYBIS'][from_curr],
            'currencyCodeTo': PROVIDER_CURRENCY_MAPS['PAYBIS'][to_curr],
            'amount': str(monetization['effective_amount']),
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
            error_msg = next((
                e['error']['message'] for key in ['paymentMethodErrors', 'payoutMethodErrors']
                if key in error_data for e in error_data[key]
            ), "Unknown Paybis error")
            return {'success': False, 'message': f"Paybis error: {error_msg}", 'status_code': quote_response.status_code}
        
        quote_data = quote_response.json()
        
        # Create transaction
        request_response = requests.post(
            'https://widget-api.sandbox.paybis.com/v2/request',
            headers=headers,
            json={
                'quoteId': quote_data['id'],
                'partnerUserId': partner_user_id,
                'locale': locale,
                'email': email
            }
        )
        
        if request_response.status_code != 200:
            return {
                'success': False,
                'message': f"Paybis request error: {request_response.status_code}",
                'status_code': request_response.status_code,
                'details': request_response.json()
            }
        
        request_data = request_response.json()
        widget_url = (
            f"https://widget.sandbox.paybis.com/?requestId={request_data['requestId']}"
            f"&apiKey={settings.PAYBIS_API_KEY}#/v2/exchange-form"
            if trans_type['type'] == 'buy' else
            f"https://widget-api.sandbox.paybis.com/v1/request/{request_data['requestId']}"
            f"?Authorization={settings.PAYBIS_API_KEY}&accept=application/json"
        )
        
        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "Transaction processed successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'request_id': request_data['requestId'],
            'quote_response': quote_data,
            'fee_details': monetization['fee_details']
        }
        
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f"Network error: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}
    except Exception as e:
        return {'success': False, 'message': f"Unexpected error: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}

def process_transak_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None,
    redirect_url: Optional[str] = None,
    theme_color: Optional[str] = None,
    hide_menu: bool = False,
    is_auto_fill: bool = False
) -> Dict:
    """Process Transak transaction with monetization."""
    from_curr, to_curr = from_currency_or_crypto.upper(), to_currency_or_crypto.upper()
    
    trans_type = _determine_transaction_type(to_curr)
    if trans_type['error']:
        return trans_type['error']
    
    # Validate currencies
    if (trans_type['type'] == 'buy' and (from_curr not in FIAT_CURRENCIES or to_curr not in CRYPTO_CURRENCIES)) or \
       (trans_type['type'] == 'sell' and (from_curr not in CRYPTO_CURRENCIES or to_curr not in FIAT_CURRENCIES)):
        return {
            'success': False,
            'message': f"{trans_type['type'].title()} transactions require {'fiat to crypto' if trans_type['type'] == 'buy' else 'crypto to fiat'}",
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    
    try:
        # Apply monetization
        monetization = _process_monetization(
            amount,
            from_curr if direction == 'from' else to_curr,
            trans_type['type']
        )
        
        base_url = "https://global-stg.transak.com" if settings.TRANSAK_SANDBOX else "https://global.transak.com"
        params = {
            'apiKey': settings.TRANSAK_API_KEY,
            'walletAddress': wallet_address,
            'productsAvailed': 'BUY' if trans_type['type'] == 'buy' else 'SELL',
            'network': get_network_for_crypto(to_curr if trans_type['type'] == 'buy' else from_curr),
            **(user_data or {})
        }
        
        if locale != 'en':
            params['locale'] = locale
        if theme_color:
            params['themeColor'] = theme_color.replace('#', '')
        if hide_menu:
            params['hideMenu'] = 'true'
        if redirect_url:
            params['redirectURL'] = redirect_url
        
        amount_key = f"{'fiat' if trans_type['type'] == 'buy' else 'crypto'}Amount" if is_auto_fill else \
                   f"default{'Fiat' if trans_type['type'] == 'buy' else 'Crypto'}Amount"
        params[amount_key] = str(monetization['effective_amount'])
        
        params.update({
            'fiatCurrency': from_curr if trans_type['type'] == 'buy' else to_curr,
            'cryptoCurrencyCode': to_curr if trans_type['type'] == 'buy' else from_curr,
        })
        
        from urllib.parse import urlencode
        widget_url = f"{base_url}?{urlencode(params)}"
        
        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "Transak widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'parameters_used': params,
            'fee_details': monetization['fee_details']
        }
        
    except Exception as e:
        return {'success': False, 'message': f"Error generating widget: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}

def process_moonpay_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None
) -> Dict:
    """Process MoonPay transaction and return widget URL."""
    from_curr, to_curr = from_currency_or_crypto.upper(), to_currency_or_crypto.upper()
    
    trans_type = _determine_transaction_type(to_curr)
    if trans_type['error']:
        return trans_type['error']
    
    # Validate currencies
    if (trans_type['type'] == 'buy' and (from_curr not in FIAT_CURRENCIES or to_curr not in CRYPTO_CURRENCIES)) or \
       (trans_type['type'] == 'sell' and (from_curr not in CRYPTO_CURRENCIES or to_curr not in FIAT_CURRENCIES)):
        return {
            'success': False,
            'message': f"{trans_type['type'].title()} transactions require {'fiat to crypto' if trans_type['type'] == 'buy' else 'crypto to fiat'}",
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    
    try:
        # Apply monetization
        monetization = _process_monetization(
            amount,
            from_curr if direction == 'from' else to_curr,
            trans_type['type']
        )
        
        base_url = ("https://buy-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://buy.moonpay.com") \
            if trans_type['type'] == 'buy' else \
            ("https://sell-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://sell.moonpay.com")
        
        widget_url = (
            f"{base_url}/?apiKey={settings.MOONPAY_API_KEY}"
            f"&walletAddress={wallet_address}"
            f"&currencyCode={PROVIDER_CURRENCY_MAPS['MOONPAY'].get(to_curr if trans_type['type'] == 'buy' else from_curr, (to_curr if trans_type['type'] == 'buy' else from_curr).lower())}"
            f"&baseCurrencyCode={from_curr if trans_type['type'] == 'buy' else to_curr}"
            f"&{'baseCurrency' if trans_type['type'] == 'buy' else 'currency'}Amount={monetization['effective_amount'] if direction == 'from' else ''}"
            f"&{'currency' if trans_type['type'] == 'buy' else 'baseCurrency'}Amount={monetization['effective_amount'] if direction == 'to' else ''}"
            f"{f'&language={locale}' if locale else ''}"
        )
        
        if user_data:
            widget_url += ''.join(f"&{key}={value}" for key, value in user_data.items())
        
        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "MoonPay widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'fee_details': monetization['fee_details']
        }
        
    except Exception as e:
        return {'success': False, 'message': f"Error generating widget: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}