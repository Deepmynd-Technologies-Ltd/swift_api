from cryptography.fernet import Fernet
from django.conf import settings

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def encrypt(plainText:str):
    f = Fernet(settings.HASHKEY)
    val = f.encrypt(plainText.encode())
    return val.decode()

def decrypt(plainText:str):
    f = Fernet(settings.HASHKEY)
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