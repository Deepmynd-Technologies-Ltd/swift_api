# utils/jwt.py
from google.auth.transport import requests
from google.oauth2 import id_token
from ninja_jwt.tokens import RefreshToken
from helper.helper import decrypt, encrypt
from wallet.models import Wallets
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
from django.conf import settings


def generate_user_wallet(user):
    mnemo = Mnemonic("english")
    phrase = mnemo.generate(strength=256)  # Generates a 24-word mnemonic phrase
    print(f"Seed Phrase: {phrase}")
    
    # Enable HD Wallet features (Note: Ensure this is safe and aligns with your security policies)
    web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/' + settings.INFURA))  # Use your Infura project ID
    web3.eth.account.enable_unaudited_hdwallet_features()
    
    account = web3.eth.account.from_mnemonic(phrase)
    
    # Encrypt the private key before saving
    encrypted_private_key = encrypt(account.key.hex())
    
    # Create the wallet instance
    wallet = Wallets.objects.create(
        address=account.address,
        private_key=encrypted_private_key,
        owner=user
    )
    
    return {"address": account.address, "phrase": phrase.split()}


def create_jwt_token(user) -> dict:
    tokens = RefreshToken.for_user(user)
    return {"refresh_token": str(tokens), "access_token": str(tokens.access_token)}

class Google:
    @staticmethod
    def validate_token(auth_token:str)-> dict|str:
        try:
            idInfo = id_token.verify_oauth2_token(auth_token, requests.Request())

            if 'accounts.google.com' in idInfo['iss']:
                return idInfo
        except:
            return "Token is not verified"

infura_url = 'https://mainnet.infura.io/v3/'+settings.INFURA
# infura_url = 'HTTP://127.0.0.1:7545'
web3 = Web3(Web3.HTTPProvider(infura_url))

def generate_user_wallet_address(user):
    mnemo = Mnemonic("english")
    phrase = mnemo.generate(strength=256)
    print(phrase)
    web3.eth.account.enable_unaudited_hdwallet_features()
    account = web3.eth.account.from_mnemonic(phrase)
    # Private Key, Address and phrase ...
    """
    Ton Tron USDT BTC Eth Sol
    {
        "phrase": "Run ddf",
        "results": [
            {
                "btc": "address",
                "privateKey": "key",
                "encrypt": "key",
            },
            {
                "eth": "address",
                "privateKey": "key",
                "encrypt": "key",
            },
        ]
    }
    {
        "identity": "btc",

    }
    """

    encrypted_private_key = encrypt(account._private_key.hex())
    Wallets.objects.create(address= account.address, private_key=encrypted_private_key, owner=user)

def make_transaction_to_wallet(key, from_address, recipient_address, amount):
    try:
        # private_key = "0x117a9b10aec16a75626fdaaf7ca99a0e2293034c3327ce4376a60e980d6937cd"
        private_key = decrypt(key)
        account = Account.from_key(private_key)
        if not web3.is_address(recipient_address):
            raise Exception("Invalid Address")

        if account.address != from_address:
            raise Exception("Incorrect address")

        value = web3.to_wei(amount, 'ether')

        nonce = web3.eth.get_transaction_count(account.address)
        balance = web3.eth.get_balance(account.address)

        if amount > web3.from_wei(balance, "ether"):
            raise Exception("Insufficient Ballance")

        transaction_params = {
            'to': recipient_address,
            'value': value,
            'nonce': nonce,
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
        }
        signed_tx = web3.eth.account.sign_transaction(transaction_params, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tr = web3.eth.get_transaction_receipt(tx_hash)
        return tr, transaction_params["gasPrice"]
    except Exception as ex:
        raise ex

def get_wallet_balance(key):
    private_key = decrypt(key)
    account = Account.from_key(private_key)
    balance = web3.eth.get_balance(account.address)
    return round(balance, 2)