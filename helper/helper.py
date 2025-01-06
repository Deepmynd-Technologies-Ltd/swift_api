from cryptography.fernet import Fernet
from core import settings
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

def generate_fernet_key():
    """Generate a valid Fernet key and update settings.HASHKEY."""
    key = Fernet.generate_key()
    print(key.decode())  # Output the key
    settings.HASHKEY = key
    return key

def fix_base64_padding(key: bytes) -> bytes:
    """Fix base64 URL-safe key padding."""
    return base64.urlsafe_b64encode(base64.urlsafe_b64decode(key.encode() + b'=='))

def get_encryption_key():
    key = settings.HASHKEY
    print(f"Original HASHKEY: {key}")
    fixed_key = fix_base64_padding(key)
    print(f"Fixed HASHKEY: {fixed_key}")
    return fixed_key

def encrypt(plainText: str):
    # Get the fixed key with proper base64 padding
    key = get_encryption_key()
    f = Fernet(key)
    val = f.encrypt(plainText.encode())
    return val.decode()

def decrypt(plainText: str):
    # Get the fixed key with proper base64 padding
    key = get_encryption_key()
    f = Fernet(key)
    val = f.decrypt(plainText.encode())
    return val.decode()

def load_public_key():
    paybis_public_key = settings.PAYBIS_KEY
    print(paybis_public_key)
    return serialization.load_pem_public_key(
        paybis_public_key.encode(),
        backend=default_backend()
    )

def verify_signature(public_key, signature, payload):
    try:
        public_key.verify(
            signature,
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512()
        )
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False