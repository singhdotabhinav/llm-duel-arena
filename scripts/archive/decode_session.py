#!/usr/bin/env python3
"""
Quick script to decode session cookie value
Run this and paste your session cookie value to see what's inside
"""
import base64
import json
import sys

def decode_session_cookie(cookie_value):
    """Decode a Starlette session cookie"""
    try:
        # Starlette session cookies are base64-encoded JSON
        # Remove any padding if needed
        padding = len(cookie_value) % 4
        if padding:
            cookie_value += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(cookie_value)
        data = json.loads(decoded)
        return data
    except Exception as e:
        return f"Error decoding: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cookie_value = sys.argv[1]
    else:
        print("Paste your session cookie value (the part after 'session='):")
        cookie_value = input().strip()
    
    decoded = decode_session_cookie(cookie_value)
    print("\n=== Decoded Session Data ===")
    print(json.dumps(decoded, indent=2))

