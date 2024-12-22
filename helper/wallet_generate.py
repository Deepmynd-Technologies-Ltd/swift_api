import base64
from eth_account import Account
from mnemonic import Mnemonic
from bitcoinlib.keys import HDKey
from solders.keypair import Keypair
from tronpy.keys import PrivateKey as TronPrivateKey
from xrpl.wallet import Wallet as XrplWallet
import hashlib
import ecdsa
import base58


# Generate a BIP39 Mnemonic
def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)


# Generate Bitcoin Bech32 (bc1) Address
def generate_btc_wallet(mnemonic, passphrase=""):
    seed = Mnemonic.to_seed(mnemonic, passphrase)
    hdkey = HDKey.from_seed(seed)
    key = hdkey.subkey_for_path("m/84'/0'/0'/0/0")  # BIP84 for Bech32
    return {
        "address": key.address(),
        "private_key": key.wif()  # Wallet Import Format
    }


# Generate Ethereum Wallet
def generate_eth_wallet(mnemonic, passphrase=""):
    # Derive seed from mnemonic and passphrase
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), ("mnemonic" + passphrase).encode(), 2048)
    # Derive Ethereum private key (BIP-44 path m/44'/60'/0'/0/0)
    private_key = hashlib.sha256(seed).hexdigest()
    account = Account.from_key(private_key)
    return {"address": account.address, "private_key": private_key}


# Generate Solana Wallet
def generate_solana_wallet(mnemonic, passphrase=""):
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), ("mnemonic" + passphrase).encode(), 2048)[:32]
    signing_key = SigningKey(seed)
    private_key = signing_key.encode().hex()
    public_key = signing_key.verify_key.encode().hex()
    return {"address": public_key, "private_key": private_key}


# Generate TON Wallet (Placeholder)
def generate_ton_wallet(mnemonic):
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), ("mnemonic" + passphrase).encode(), 2048)[:32]
    private_key = seed.hex()
    public_key = hashlib.sha256(seed).digest()
    address = base64.urlsafe_b64encode(public_key[:32]).decode().rstrip("=")
    return {"address": f"ton1{address}", "private_key": private_key}


# Generate Tron Wallet
def generate_tron_wallet(mnemonic, passphrase=""):
    seed = Mnemonic.to_seed(mnemonic, passphrase)
    hdkey = HDKey.from_seed(seed)
    key = hdkey.subkey_for_path("m/44'/195'/0'/0/0")  # BIP44 for Tron
    # private_key = key.private_byte_hex
    private_key = key.private_hex
    tron_key = TronPrivateKey(bytes.fromhex(private_key))
    return {
        "address": tron_key.public_key.to_base58check_address(),
        # "address": tron_key.public_key.to_base58check_address(),
        "private_key": private_key
    }


# Generate Ripple Wallet
def generate_ripple_wallet(mnemonic, passphrase=""):
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), ("mnemonic" + passphrase).encode(), 2048)[:32]
    sk = ecdsa.SigningKey.from_string(seed, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    private_key = sk.to_string().hex()
    public_key = vk.to_string().hex()

    # Ripple address encoding
    address = base58.b58encode_check(b"\x00" + hashlib.new("ripemd160", hashlib.sha256(vk.to_string()).digest()).digest())
    return {"address": address.decode(), "private_key": private_key}


# Generate Tether Wallet (USDT-ERC20)
def generate_tether_wallet(mnemonic, passphrase=""):
    return generate_eth_wallet(mnemonic, passphrase)


# Generate Wallets for All Blockchains
def generate_all_wallets(mnemonic):
    return {
        # "Bitcoin (Bech32)": generate_btc_wallet(mnemonic),
        # "Tron": generate_tron_wallet(mnemonic),
        # "Ethereum": generate_eth_wallet(mnemonic),
        # "Solana": generate_solana_wallet(mnemonic),
        # "TON": generate_ton_wallet(mnemonic),
        # "Tether (USDT-ERC20)": generate_tether_wallet(mnemonic),
        # "Ripple": generate_ripple_wallet(mnemonic)
    }


# Main Function
if __name__ == "__main__":
    # Generate Mnemonic Phrase
    mnemonic_phrase = generate_mnemonic()
    print(f"Mnemonic Phrase: {mnemonic_phrase}\n")

    # Generate Wallets
    wallets = generate_all_wallets(mnemonic_phrase)
    for blockchain, wallet in wallets.items():
        print(f"{blockchain} Wallet:")
        print(f"  Address: {wallet['address']}")
        print(f"  Private Key: {wallet['private_key']}\n")
