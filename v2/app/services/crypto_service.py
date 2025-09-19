"""
Cryptography service for CyberVantage.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app

class CryptoService:
    """
    Service for encryption and decryption operations.
    """
    
    def __init__(self):
        """
        Initialize the cryptography service with secret key.
        """
        self.secret_key = os.getenv('SECRET_KEY', 'default-dev-key').encode()
    
    def _get_key(self, salt=None):
        """
        Generate a key using PBKDF2HMAC.
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        return key, salt
    
    def encrypt(self, data):
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data (str): Data to encrypt
            
        Returns:
            dict: Dictionary containing encrypted data and salt
        """
        try:
            salt = os.urandom(16)
            key, _ = self._get_key(salt)
            
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            
            return {
                'encrypted': base64.urlsafe_b64encode(encrypted_data).decode(),
                'salt': base64.urlsafe_b64encode(salt).decode()
            }
        except Exception as e:
            current_app.logger.error(f"Encryption error: {str(e)}")
            return None
    
    def decrypt(self, encrypted_data, salt):
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data (str): Base64 encoded encrypted data
            salt (str): Base64 encoded salt used for key derivation
            
        Returns:
            str: Decrypted data
        """
        try:
            decoded_salt = base64.urlsafe_b64decode(salt.encode())
            key, _ = self._get_key(decoded_salt)
            
            f = Fernet(key)
            decrypted_data = f.decrypt(base64.urlsafe_b64decode(encrypted_data.encode()))
            
            return decrypted_data.decode()
        except Exception as e:
            current_app.logger.error(f"Decryption error: {str(e)}")
            return None

# Create service instance
crypto_service = CryptoService()

# Export functions
encrypt = crypto_service.encrypt
decrypt = crypto_service.decrypt