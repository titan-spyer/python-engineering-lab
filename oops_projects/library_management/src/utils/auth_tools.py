import hashlib
import secrets
from typing import Tuple, Optional


class AuthTools:
    """
    Authentication and authorization utilities.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using SHA-256.
        Note: In production, use bcrypt or argon2 instead.
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Add a salt for better security
        salt = secrets.token_hex(8)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        """
        if not password or not password_hash:
            return False
        
        try:
            # Extract salt and hash
            if '$' in password_hash:
                salt, hash_value = password_hash.split('$', 1)
                hash_obj = hashlib.sha256((password + salt).encode())
                return hash_obj.hexdigest() == hash_value
            else:
                # Legacy hash without salt
                hash_obj = hashlib.sha256(password.encode())
                return hash_obj.hexdigest() == password_hash
        except Exception:
            return False
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Generate a temporary password."""
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def check_permission(user_role: int, required_role: int) -> bool:
        """Check if user has required permission level."""
        return user_role >= required_role