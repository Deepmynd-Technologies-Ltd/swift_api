from typing import List
from bip_utils import (
   Bip39SeedGenerator, Bip44,
    Bip44Coins
)
from bitcoinlib.keys import HDKey
from mnemonic import Mnemonic

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

    # Bitcoin (BTC)
    btc_seed = Mnemonic.to_seed(seed_phrase)
    hdkey = HDKey.from_seed(btc_seed)

    btc_wallet = hdkey.subkey_for_path("m/84'/0'/0'/0/0")
    btc_info = WalletInfoResponse(name="Bitcoin", symbols= Symbols.BTC, address=btc_wallet.address(), private_key=btc_wallet.wif(), balance=get_btc_balance_and_history(btc_wallet.address()))
    wallets.append(btc_info)

    # Ethereum (ETH)
    eth_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).DeriveDefaultPath()
    eth_info = WalletInfoResponse(name="Ethereum", symbols= Symbols.ETH, address=eth_wallet.PublicKey().ToAddress(),private_key= eth_wallet.PrivateKey().Raw().ToHex(),balance= get_eth_balance_and_history(eth_wallet.PublicKey().ToAddress()))
    wallets.append(eth_info)

    # USDT BEP20
    usdt_info =  WalletInfoResponse(name="USDT BEP20", symbols= Symbols.USDT, address=eth_wallet.PublicKey().ToAddress(),private_key=eth_wallet.PrivateKey().Raw().ToHex(),balance=get_usdt_balance(eth_wallet.PublicKey().ToAddress()))
    wallets.append(usdt_info)

    # Solana (SOL)
    sol_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA).DeriveDefaultPath()
    sol_info = WalletInfoResponse(name="Solana", symbols= Symbols.SOL, address=sol_wallet.PublicKey().ToAddress(),private_key= sol_wallet.PrivateKey().Raw().ToHex(),balance= get_sol_balance_and_history(sol_wallet.PublicKey().ToAddress()))
    wallets.append(sol_info)

    # Tron (TRX)
    trx_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON).DeriveDefaultPath()
    tron_balance = get_tron_balance(trx_wallet.PublicKey().ToAddress())
    tron_info = WalletInfoResponse(name="Tron", symbols= Symbols.TRON, address=trx_wallet.PublicKey().ToAddress(),private_key= trx_wallet.PrivateKey().Raw().ToHex(),balance= float(tron_balance))
    wallets.append(tron_info)

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
    doge_info =  WalletInfoResponse(name="Doge coin", symbols= Symbols.DODGE, address=doge_wallet.PublicKey().ToAddress(),private_key=doge_wallet.PrivateKey().Raw().ToHex(),balance=get_dodge_balance(doge_wallet.PublicKey().ToAddress()))
    wallets.append(doge_info)

    # BNB Wallets
    binance_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.BINANCE_SMART_CHAIN).DeriveDefaultPath()
    bnb_info = WalletInfoResponse(name="BNB BEP20", symbols= Symbols.BNB, address=binance_wallet.PublicKey().ToAddress(),private_key=binance_wallet.PrivateKey().Raw().ToHex(),balance=get_bnb_balance_and_history(binance_wallet.PublicKey().ToAddress()))
    wallets.append(bnb_info)
    return wallets