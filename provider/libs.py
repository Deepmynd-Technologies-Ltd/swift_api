from cryptography.fernet import Fernet
from django.conf import settings

# Load the key from settings
key = settings.ENCRYPTION_KEY.encode()  # Convert string to bytes
cipher_suite = Fernet(key)

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data):
    return cipher_suite.decrypt(encrypted_data).decode()