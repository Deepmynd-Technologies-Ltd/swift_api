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
    'TRANSAK': {'ETH': 'ethereum','SOL': 'solana', 'BNB': 'binancesmartchain','BTC': 'bitcoin','DOGE': 'dogecoin','USDT': 'ethereum',
    },
    'MOONPAY': {'ETH': 'eth','SOL': 'sol','BNB': 'bnb','BTC': 'btc','DOGE': 'doge','USDT': 'usdt',
    }
}

MONETIZATION_CONFIG = {
    'base_fee_percent': Decimal('0.01'),
    'fee_tiers': {'buy': Decimal('0.005'), 'sell': Decimal('0.007')},
    'min_fee': {
        'USD': Decimal('0.50'),
        'EUR': Decimal('0.45'),
        'GBP': Decimal('0.40'),
        'NGN': Decimal('200'),
    },
    'revenue_share': Decimal('0.3'),
    'settlement_wallets': {
        'BTC': 'your_btc_wallet_address',
        'ETH': 'your_eth_wallet_address',
        'USDT': 'your_usdt_wallet_address',
        'USD': 'your_bank_account_id',
        'EUR': 'your_eur_bank_account_id',
    }
}

def get_network_for_crypto(crypto_code: str) -> str:
    """Map cryptocurrency codes to their network names."""
    return PROVIDER_CURRENCY_MAPS['TRANSAK'].get(crypto_code.upper(), 'ethereum')

def calculate_monetization_fees(amount: Decimal, currency: str, transaction_type: str) -> Dict:
    """Calculate fees based on monetization strategy."""
    config = MONETIZATION_CONFIG
    currency = currency.upper()
    
    base_fee = amount * config['base_fee_percent']
    tier_fee = amount * config['fee_tiers'].get(transaction_type, Decimal('0'))
    total_fee = max(base_fee + tier_fee, config['min_fee'].get(currency, Decimal('0')))
    total_fee = min(total_fee, amount)
    
    company_share = total_fee * config['revenue_share']
    
    return {
        'gross_amount': amount,
        'net_amount': amount - total_fee,
        'total_fee': total_fee,
        'company_share': company_share,
        'provider_share': total_fee - company_share,
        'currency': currency,
        'transaction_type': transaction_type
    }

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
            'message': 'Selling requires crypto as from_currency',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    if transaction_type == 'buy' and from_curr not in FIAT_CURRENCIES:
        return {
            'success': False,
            'message': 'Buying requires fiat as from_currency',
            'status_code': HTTPStatusCode.BAD_REQUEST
        }
    return None

def _process_monetization(amount: Decimal, currency: str, transaction_type: str, 
                         user_id: Optional[str], apply_monetization: bool) -> tuple:
    """Process monetization fees if enabled."""
    if not apply_monetization:
        return amount, None
    
    fee_details = calculate_monetization_fees(amount, currency, transaction_type)
    store_fee_record(user_id, transaction_type, fee_details)
    return fee_details['net_amount'], fee_details

def process_paybis_transaction(
    from_currency: str,
    to_currency: str,
    amount: Decimal,
    partner_user_id: str,
    email: str,
    direction: str = 'from',
    locale: str = 'en',
    apply_monetization: bool = True
) -> Dict:
    """Handle Paybis transactions with monetization."""
    from_curr, to_curr = from_currency.upper(), to_currency.upper()
    
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
        # Process monetization
        effective_amount, fee_details = _process_monetization(
            amount, from_curr if direction == 'from' else to_curr, 
            trans_type['type'], partner_user_id, apply_monetization
        )
        
        # Get quote
        quote_payload = {
            'currencyCodeFrom': PROVIDER_CURRENCY_MAPS['PAYBIS'][from_curr],
            'currencyCodeTo': PROVIDER_CURRENCY_MAPS['PAYBIS'][to_curr],
            'amount': str(effective_amount),
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
        
        response = {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "Transaction processed successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'request_id': request_data['requestId'],
            'quote_response': quote_data,
        }
        
        if fee_details:
            response['fee_details'] = fee_details
            initiate_settlement(fee_details['company_share'], fee_details['currency'], partner_user_id)
        
        return response
        
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f"Network error: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}
    except Exception as e:
        return {'success': False, 'message': f"Unexpected error: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}

def process_transak_transaction(
    from_currency: str,
    to_currency: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None,
    redirect_url: Optional[str] = None,
    theme_color: Optional[str] = None,
    hide_menu: bool = False,
    is_auto_fill: bool = False,
    apply_monetization: bool = True
) -> Dict:
    """Process Transak transaction with monetization."""
    from_curr, to_curr = from_currency.upper(), to_currency.upper()
    
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
        effective_amount, fee_details = _process_monetization(
            amount, from_curr if direction == 'from' else to_curr,
            trans_type['type'], user_data.get('id') if user_data else None, apply_monetization
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
        params[amount_key] = str(effective_amount)
        
        params.update({
            'fiatCurrency': from_curr if trans_type['type'] == 'buy' else to_curr,
            'cryptoCurrencyCode': to_curr if trans_type['type'] == 'buy' else from_curr,
        })
        
        from urllib.parse import urlencode
        widget_url = f"{base_url}?{urlencode(params)}"
        
        response = {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "Transak widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'parameters_used': params
        }
        
        if fee_details:
            response['fee_details'] = fee_details
            initiate_settlement(fee_details['company_share'], fee_details['currency'], user_data.get('id') if user_data else None)
        
        return response
        
    except Exception as e:
        return {'success': False, 'message': f"Error generating widget: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}

def process_moonpay_transaction(
    from_currency: str,
    to_currency: str,
    amount: Decimal,
    wallet_address: str,
    direction: str = 'from',
    locale: str = 'en',
    user_data: Optional[Dict] = None
) -> Dict:
    """Process MoonPay transaction and return widget URL."""
    from_curr, to_curr = from_currency.upper(), to_currency.upper()
    
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
        base_url = ("https://buy-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://buy.moonpay.com") \
            if trans_type['type'] == 'buy' else \
            ("https://sell-staging.moonpay.com" if settings.MOONPAY_SANDBOX else "https://sell.moonpay.com")
        
        widget_url = (
            f"{base_url}/?apiKey={settings.MOONPAY_API_KEY}"
            f"&walletAddress={wallet_address}"
            f"&currencyCode={PROVIDER_CURRENCY_MAPS['MOONPAY'].get(to_curr if trans_type['type'] == 'buy' else from_curr, (to_curr if trans_type['type'] == 'buy' else from_curr).lower())}"
            f"&baseCurrencyCode={from_curr if trans_type['type'] == 'buy' else to_curr}"
            f"&{'baseCurrency' if trans_type['type'] == 'buy' else 'currency'}Amount={amount if direction == 'from' else ''}"
            f"&{'currency' if trans_type['type'] == 'buy' else 'baseCurrency'}Amount={amount if direction == 'to' else ''}"
            f"{f'&language={locale}' if locale else ''}"
        )
        
        if user_data:
            widget_url += ''.join(f"&{key}={value}" for key, value in user_data.items())
        
        return {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': trans_type['type'],
            'message': "MoonPay widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS
        }
        
    except Exception as e:
        return {'success': False, 'message': f"Error generating widget: {str(e)}", 'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR}

# Helper functions (unchanged)
def store_fee_record(user_id: Optional[str], transaction_type: str, fee_details: Dict) -> bool:
    """Store fee record in database."""
    try:
        return True
    except Exception as e:
        print(f"Error storing fee record: {str(e)}")
        return False

def initiate_settlement(amount: Decimal, currency: str, user_id: Optional[str]) -> bool:
    """Initiate automatic settlement."""
    try:
        currency = currency.upper()
        wallet_address = MONETIZATION_CONFIG['settlement_wallets'].get(currency)
        if wallet_address:
            print(f"Would settle {amount} {currency} to wallet {wallet_address}")
            return True
        print(f"No settlement method for {currency}")
        return False
    except Exception as e:
        print(f"Error initiating settlement: {str(e)}")
        return False