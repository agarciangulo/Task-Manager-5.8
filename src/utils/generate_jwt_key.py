#!/usr/bin/env python3
"""
Generate a secure JWT secret key for the authentication system.
"""

import secrets
import base64
import os

def generate_jwt_key():
    """Generate a secure JWT secret key."""
    # Generate 32 bytes of random data
    random_bytes = secrets.token_bytes(32)
    
    # Use URL-safe base64 encoding to avoid special characters
    jwt_key = secrets.token_urlsafe(32)
    
    return jwt_key

def main():
    """Generate and display JWT key."""
    print("Generating secure JWT secret key...")
    print("=" * 50)
    
    jwt_key = generate_jwt_key()
    
    print(f"JWT_SECRET_KEY={jwt_key}")
    print()
    print("Add this to your .env file:")
    print(f"JWT_SECRET_KEY={jwt_key}")
    print()
    print("Or set it as an environment variable:")
    print(f"export JWT_SECRET_KEY='{jwt_key}'")
    print()
    print("⚠️  Keep this key secure and don't share it!")
    print("⚠️  Use different keys for development and production!")
    print()
    print("✅ This key is URL-safe and compatible with .env files!")

if __name__ == "__main__":
    main() 