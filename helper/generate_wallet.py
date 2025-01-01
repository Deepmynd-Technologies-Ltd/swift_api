from typing import List
from bip_utils import (
   Bip39SeedGenerator, Bip44,
    Bip44Coins
)
from bitcoinlib.keys import HDKey
from mnemonic import Mnemonic
from django.conf import settings
from helper.coingeko_api import get_coins_value
from helper.wallet_balance import get_bnb_balance_and_history, get_btc_balance_and_history, get_dodge_balance, get_eth_balance_and_history, get_sol_balance_and_history, get_tron_balance, get_usdt_balance
from home.wallet_schema import Symbols, WalletInfoResponse

def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)

def generate_wallets_from_seed(seed_phrase)-> List[WalletInfoResponse]:
    # Generate seed from mnemonic
    seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()

    # Derive wallets for each blockchain
    wallets = []
    coinValue = get_coins_value()
    base_url = f"{settings.SITE_URL}/media/icons"

    # Bitcoin (BTC)
    btc_seed = Mnemonic.to_seed(seed_phrase)
    hdkey = HDKey.from_seed(btc_seed)
    btc_wallet = hdkey.subkey_for_path("m/84'/0'/0'/0/0")
    btc_balance = get_btc_balance_and_history(btc_wallet.address())

    # Bitcoin Calculation
    price_bitcoin = btc_balance * coinValue['bitcoin']['usd']
    change_bitcoin_hr = coinValue['bitcoin']['usd_24h_change']
    volume_bitcoin = coinValue['bitcoin']['usd']
    btc_info = WalletInfoResponse(name="Bitcoin", icon_url=f'{base_url}/btc_icon.svg', idName='bitcoin',symbols= Symbols.BTC, volume=volume_bitcoin, address=btc_wallet.address(), private_key=btc_wallet.wif(), balance=round(btc_balance, 6), price=price_bitcoin, changes=round(change_bitcoin_hr, 3))
    wallets.append(btc_info)

    # Ethereum (ETH)
    eth_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).DeriveDefaultPath()
    eth_balance = get_eth_balance_and_history(eth_wallet.PublicKey().ToAddress())

    # ethereum Calculate
    price_ethereum =eth_balance * coinValue['ethereum']['usd']
    change_ethereum_hr = coinValue['ethereum']['usd_24h_change']
    volume_ethereum = coinValue['ethereum']['usd']
    eth_info = WalletInfoResponse(name="Ethereum", icon_url=f'{base_url}/eth_icon.svg', idName= 'ethereum', symbols= Symbols.ETH, volume=volume_ethereum, address=eth_wallet.PublicKey().ToAddress(),private_key= eth_wallet.PrivateKey().Raw().ToHex(),balance= round(eth_balance,6), price=price_ethereum, changes=round(change_ethereum_hr, 3))
    wallets.append(eth_info)

    # USDT BEP20
    usdt_balance = get_usdt_balance(eth_wallet.PublicKey().ToAddress())

    price_tether =usdt_balance * coinValue['tether']['usd']
    change_tether_hr = coinValue['tether']['usd_24h_change']
    volume_tether = coinValue['tether']['usd']
    usdt_info =  WalletInfoResponse(name="USDT BEP20", icon_url=f'{base_url}/usdt_icon.svg', idName='tether', symbols= Symbols.USDT, volume=volume_tether, address=eth_wallet.PublicKey().ToAddress(),private_key=eth_wallet.PrivateKey().Raw().ToHex(),balance=round(usdt_balance, 6), price=price_tether, changes=round(change_tether_hr, 3))
    wallets.append(usdt_info)

    # Solana (SOL)
    sol_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA).DeriveDefaultPath()
    sol_balance = get_sol_balance_and_history(sol_wallet.PublicKey().ToAddress())

    price_solana =sol_balance * coinValue['solana']['usd']
    change_solana_hr = coinValue['solana']['usd_24h_change']
    volume_solana = coinValue['solana']['usd']
    sol_info = WalletInfoResponse(name="Solana", icon_url=f'{base_url}/sol_icon.svg', idName='solana', symbols= Symbols.SOL, volume=volume_solana, address=sol_wallet.PublicKey().ToAddress(),private_key= sol_wallet.PrivateKey().Raw().ToHex(),balance= round(sol_balance, 6), price=price_solana, changes=round(change_solana_hr, 3))
    wallets.append(sol_info)

    # Tron (TRX)
    # trx_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON).DeriveDefaultPath()
    # tron_balance = get_tron_balance(trx_wallet.PublicKey().ToAddress())
    # tron_info = WalletInfoResponse(name="Tron", symbols= Symbols.TRON, address=trx_wallet.PublicKey().ToAddress(),private_key= trx_wallet.PrivateKey().Raw().ToHex(),balance= float(tron_balance))
    # wallets.append(tron_info)

    # XRP (Ripple)
    xrp_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.RIPPLE).DeriveDefaultPath()
    # wallets["XRP"]
    xrp_wallet_info = {
      "name": "Ripple",
      "address": xrp_wallet.PublicKey().ToAddress(),
      "private_key": xrp_wallet.PrivateKey().Raw().ToHex(),
      "balance": 0,
    }

    # Doge Wallets
    doge_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.DOGECOIN).DeriveDefaultPath()
    doge_balance = get_dodge_balance(doge_wallet.PublicKey().ToAddress())

    price_doge =doge_balance * coinValue['dogecoin']['usd']
    change_doge_hr = coinValue['dogecoin']['usd_24h_change']
    volume_doge = coinValue['dogecoin']['usd']

    doge_info =  WalletInfoResponse(name="Doge coin", icon_url=f'{base_url}/doge_icon.svg', idName='dogecoin', symbols= Symbols.DODGE, volume=volume_doge, address=doge_wallet.PublicKey().ToAddress(),private_key=doge_wallet.PrivateKey().Raw().ToHex(),balance=round(doge_balance, 6), price=price_doge, changes=round(change_doge_hr, 3))
    wallets.append(doge_info)

    # BNB Wallets
    binance_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.BINANCE_SMART_CHAIN).DeriveDefaultPath()
    bnb_balance = get_bnb_balance_and_history(binance_wallet.PublicKey().ToAddress())

    price_bnb =bnb_balance * coinValue['binancecoin']['usd']
    change_bnb_hr = coinValue['binancecoin']['usd_24h_change']
    volume_bnb = coinValue['binancecoin']['usd']

    bnb_info = WalletInfoResponse(name="BNB BEP20", icon_url=f'{base_url}/bnb_iicon.svg', idName='binancecoin', symbols= Symbols.BNB, volume=volume_bnb, address=binance_wallet.PublicKey().ToAddress(),private_key=binance_wallet.PrivateKey().Raw().ToHex(),balance=round(bnb_balance, 6), price=round(price_bnb, 6), changes=round(change_bnb_hr, 3))
    wallets.append(bnb_info)
    return wallets