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

# Monetization Configuration
MONETIZATION_CONFIG = {
    'base_fee_percent': Decimal('0.01'),  # 1%
    
    'fee_tiers': {
        'buy': Decimal('0.005'),  # 0.5%
        'sell': Decimal('0.007'),  # 0.7%
    },
    
    'min_fee': {
        'USD': Decimal('0.50'),
        'EUR': Decimal('0.45'),
        'GBP': Decimal('0.40'),
        'NGN': Decimal('200'),
    },
    
    'revenue_share': Decimal('0.3'),
    
    # Your company's wallet addresses for automatic settlements
    'settlement_wallets': {
        'BTC': 'your_btc_wallet_address',
        'ETH': 'your_eth_wallet_address',
        'USDT': 'your_usdt_wallet_address',
        'USD': 'your_bank_account_id',
        'EUR': 'your_eur_bank_account_id',
    }
}

def get_network_for_crypto(crypto_code: str) -> str:
    """
    Helper function to map cryptocurrency codes to their correct network names
    """
    TRANSAK_CRYPTO_NETWORK_MAP = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum', 
        'BNB': 'bsc',
        'USDT': 'ethereum',
        'USDC': 'ethereum',
        'SOL': 'solana',
        'DOGE': 'dogecoin',
        # ... (rest of the network mappings from original code)
    }
    
    return TRANSAK_CRYPTO_NETWORK_MAP.get(crypto_code.upper(), 'ethereum')

def calculate_monetization_fees(amount: Decimal, currency: str, transaction_type: str) -> Dict:
    """
    Calculate fees based on monetization strategy
    """
    config = MONETIZATION_CONFIG
    currency = currency.upper()
    
    # Calculate percentage fees
    base_fee = amount * config['base_fee_percent']
    tier_fee = amount * config['fee_tiers'].get(transaction_type, Decimal('0'))
    total_percentage_fee = base_fee + tier_fee
    
    # Check against minimum fee
    min_fee = config['min_fee'].get(currency, Decimal('0'))
    total_fee = max(total_percentage_fee, min_fee)
    
    # Ensure we don't take more than the transaction amount
    total_fee = min(total_fee, amount)
    
    # Calculate shares
    company_share = total_fee * config['revenue_share']
    provider_share = total_fee - company_share
    
    return {
        'gross_amount': amount,
        'net_amount': amount - total_fee,
        'total_fee': total_fee,
        'company_share': company_share,
        'provider_share': provider_share,
        'currency': currency,
        'transaction_type': transaction_type
    }

def process_paybis_transaction(
    from_currency_or_crypto: str,
    to_currency_or_crypto: str,
    amount: Decimal,
    partner_user_id: str,
    email: str,
    direction: str = 'from',
    locale: str = 'en',
    apply_monetization: bool = True
) -> Dict:
    """
    Function to handle Paybis transactions (buy/sell) with monetization
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
        # Calculate fees if monetization is enabled
        effective_amount = amount
        fee_details = None
        
        if apply_monetization:
            fee_currency = from_curr if direction == 'from' else to_curr
            fee_details = calculate_monetization_fees(amount, fee_currency, transaction_type)
            effective_amount = fee_details['net_amount']
            
            store_fee_record(
                user_id=partner_user_id,
                transaction_type=transaction_type,
                fee_details=fee_details
            )

        quote_payload = {
            'currencyCodeFrom': PAYBIS_CRYPTO_CURRENCY_MAP[from_curr],
            'currencyCodeTo': PAYBIS_CRYPTO_CURRENCY_MAP[to_curr],
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

        response = {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': transaction_type,
            'message': "Transaction processed successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'request_id': request_id,
            'quote_response': quote_data,
        }

        if fee_details:
            response['fee_details'] = fee_details
            # Automatically initiate settlement for your share
            initiate_settlement(fee_details['company_share'], fee_details['currency'], partner_user_id)

        return response

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
    user_data: Optional[Dict] = None,
    redirect_url: Optional[str] = None,
    theme_color: Optional[str] = None,
    hide_menu: bool = False,
    is_auto_fill: bool = False,
    apply_monetization: bool = True
) -> Dict:
    """
    Function for Transak transaction processing with monetization
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
        # Calculate fees if monetization is enabled
        effective_amount = amount
        fee_details = None
        
        if apply_monetization:
            # Determine which currency to apply fees to
            fee_currency = from_curr if direction == 'from' else to_curr
            fee_details = calculate_monetization_fees(amount, fee_currency, transaction_type)
            effective_amount = fee_details['net_amount']
            
            # Store fee details in database for settlement tracking
            store_fee_record(
                user_id=user_data.get('id') if user_data else None,
                transaction_type=transaction_type,
                fee_details=fee_details
            )

        base_url = "https://global-stg.transak.com" if settings.TRANSAK_SANDBOX else "https://global.transak.com"

        params = {
            'apiKey': settings.TRANSAK_API_KEY,
            'walletAddress': wallet_address,
        }
        
        if locale != 'en':
            params['locale'] = locale
        
        if theme_color:
            params['themeColor'] = theme_color.replace('#', '')  # Remove # if present

        if hide_menu:
            params['hideMenu'] = 'true'
            
        if redirect_url:
            params['redirectURL'] = redirect_url
        
        if transaction_type == 'buy':
            params.update({
                'productsAvailed': 'BUY',
                'fiatCurrency': from_curr,
                'cryptoCurrencyCode': to_curr,
                'network': get_network_for_crypto(to_curr),
            })
            
            if direction == 'from':
                if is_auto_fill:
                    params['fiatAmount'] = str(effective_amount)  # Fixed amount
                else:
                    params['defaultFiatAmount'] = str(effective_amount)  # Default, user can change
            else:
                if is_auto_fill:
                    params['cryptoAmount'] = str(effective_amount)  # Fixed amount
                else:
                    params['defaultCryptoAmount'] = str(effective_amount)  # Default, user can change
                    
        else:
            params.update({
                'productsAvailed': 'SELL',
                'cryptoCurrencyCode': from_curr,
                'fiatCurrency': to_curr,
                'network': get_network_for_crypto(from_curr),
            })
            
            if direction == 'from':
                if is_auto_fill:
                    params['cryptoAmount'] = str(effective_amount)  # Fixed amount
                else:
                    params['defaultCryptoAmount'] = str(effective_amount)  # Default, user can change
            else:
                if is_auto_fill:
                    params['fiatAmount'] = str(effective_amount)  # Fixed amount
                else:
                    params['defaultFiatAmount'] = str(effective_amount)  # Default, user can change
        
        if user_data:
            user_data_mapping = {
                'email': 'email',
                'first_name': 'firstName', 
                'last_name': 'lastName',
                'phone': 'mobileNumber',
                'address': 'address',
                'country_code': 'countryCode',
            }
            
            for key, value in user_data.items():
                transak_key = user_data_mapping.get(key, key)
                if transak_key in ['email', 'firstName', 'lastName', 'mobileNumber', 'address', 'countryCode', 'userData']:
                    params[transak_key] = value
        
        from urllib.parse import urlencode
        query_string = urlencode(params)
        widget_url = f"{base_url}?{query_string}"
        
        response = {
            'success': True,
            'widget_url': widget_url,
            'transaction_type': transaction_type,
            'message': "Transak widget URL generated successfully",
            'status_code': HTTPStatusCode.SUCCESS,
            'parameters_used': params
        }

        if fee_details:
            response['fee_details'] = fee_details
            initiate_settlement(fee_details['company_share'], fee_details['currency'], user_data.get('id') if user_data else None)

        return response
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error generating Transak widget: {str(e)}",
            'status_code': HTTPStatusCode.INTERNAL_SERVER_ERROR
        }

# Helper functions for monetization tracking and settlement
def store_fee_record(user_id: Optional[str], transaction_type: str, fee_details: Dict) -> bool:
    """
    Store fee record in database for reconciliation
    
    In a real implementation, this would connect to your database
    """
    # This is a placeholder - implement your actual database logic here
    try:
        # Example pseudocode:
        # FeeRecord.objects.create(
        #     user_id=user_id,
        #     transaction_type=transaction_type,
        #     gross_amount=fee_details['gross_amount'],
        #     fee_amount=fee_details['total_fee'],
        #     company_share=fee_details['company_share'],
        #     currency=fee_details['currency'],
        #     status='pending'
        # )
        return True
    except Exception as e:
        print(f"Error storing fee record: {str(e)}")
        return False

def initiate_settlement(amount: Decimal, currency: str, user_id: Optional[str]) -> bool:
    """
    Initiate automatic settlement of your company's share
    
    This would connect to your payment processing system
    """
    # This is a placeholder - implement your actual settlement logic here
    try:
        config = MONETIZATION_CONFIG
        currency = currency.upper()
        
        # For crypto settlements
        if currency in CRYPTO_CURRENCIES:
            wallet_address = config['settlement_wallets'].get(currency)
            if wallet_address:
                # Pseudocode for crypto transfer:
                # crypto_transfer(
                #     amount=amount,
                #     currency=currency,
                #     to_address=wal_address,
                #     memo=f"Revenue share for user {user_id}"
                # )
                print(f"Would settle {amount} {currency} to wallet {wallet_address}")
                return True
        
        # For fiat settlements
        elif currency in FIAT_CURRENCIES:
            account_id = config['settlement_wallets'].get(currency)
            if account_id:
                # Pseudocode for bank transfer:
                # bank_transfer(
                #     amount=amount,
                #     currency=currency,
                #     to_account=account_id,
                #     reference=f"Revenue share {user_id}"
                # )
                print(f"Would settle {amount} {currency} to bank account {account_id}")
                return True
        
        print(f"No settlement method configured for {currency}")
        return False
        
    except Exception as e:
        print(f"Error initiating settlement: {str(e)}")
        return False

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

