"""Generate a Fernet key for ENCRYPTION_KEY. Run: python scripts/gen_encryption_key.py"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    print(Fernet.generate_key().decode())
