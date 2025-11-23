#!/usr/bin/env python3
"""
Quick script to check if APP_SECRET_KEY is properly configured
"""
import os
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv("APP_SECRET_KEY", "")

print("=" * 60)
print("Session Configuration Check")
print("=" * 60)

if not secret_key:
    print("❌ APP_SECRET_KEY is NOT set in .env file")
    print("\nPlease add to your .env file:")
    print("APP_SECRET_KEY=your-secure-random-key-minimum-32-characters")
elif secret_key == "change_me":
    print("❌ APP_SECRET_KEY is still set to default 'change_me'")
    print("\nPlease change it to a secure random key in your .env file")
elif len(secret_key) < 32:
    print(f"⚠️  APP_SECRET_KEY is too short ({len(secret_key)} characters)")
    print("Recommendation: Use at least 32 characters for security")
else:
    print(f"✅ APP_SECRET_KEY is set ({len(secret_key)} characters)")
    print(f"   First 10 chars: {secret_key[:10]}...")

print("\n" + "=" * 60)
print("Next Steps:")
print("1. If APP_SECRET_KEY is not set or is 'change_me', update your .env file")
print("2. Restart your application server")
print("3. Clear browser cookies for localhost:8000")
print("4. Try login again")
print("=" * 60)

