from cryptography.fernet import Fernet
import os
import base64
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY must be set in environment variables")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str | None:
    """
    Encrypts a token and returns base64-encoded encrypted value.

    Returns None if the input token is falsy (empty string or None) so callers
    can pass through unset values without special-casing them here.
    """
    if not token:
        return None
    encrypted = cipher_suite.encrypt(token.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str | None:
    """
    Decrypts a base64-encoded encrypted token.

    Returns None if the input is falsy, mirroring encrypt_token's behaviour
    so a round-trip on an unset value is a no-op.
    """
    if not encrypted_token:
        return None
    decoded = base64.urlsafe_b64decode(encrypted_token.encode())
    decrypted = cipher_suite.decrypt(decoded)
    return decrypted.decode()
