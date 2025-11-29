#!/usr/bin/env python3
"""
Quick setup script to generate a secure secret key for authentication.
Run this to create a .env file with a secure APP_SECRET_KEY.
"""

import secrets
import os

def generate_secret_key(length=64):
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(length)

def setup_env_file():
    """Create or update .env file with secure secret key"""
    env_example_path = "env.example"
    env_path = ".env"
    
    # Check if .env already exists
    if os.path.exists(env_path):
        print(f"✓ {env_path} already exists")
        
        # Check if it has a secret key
        with open(env_path, 'r') as f:
            content = f.read()
            if 'APP_SECRET_KEY=change_me' in content or 'APP_SECRET_KEY=' not in content:
                print("⚠️  Warning: APP_SECRET_KEY not properly set in .env")
                update = input("Generate a new secure secret key? (y/n): ")
                if update.lower() == 'y':
                    # Generate new key
                    secret_key = generate_secret_key()
                    
                    # Update the file
                    updated_content = content.replace(
                        'APP_SECRET_KEY=change_me_to_random_secret_key_minimum_32_characters',
                        f'APP_SECRET_KEY={secret_key}'
                    )
                    
                    # If pattern not found, append it
                    if updated_content == content:
                        if 'APP_SECRET_KEY=' in content:
                            # Replace existing key
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if line.startswith('APP_SECRET_KEY='):
                                    lines[i] = f'APP_SECRET_KEY={secret_key}'
                            updated_content = '\n'.join(lines)
                        else:
                            # Add it
                            updated_content = f'APP_SECRET_KEY={secret_key}\n' + content
                    
                    with open(env_path, 'w') as f:
                        f.write(updated_content)
                    
                    print(f"✓ Generated new secure secret key in {env_path}")
                    print(f"  Key: {secret_key[:20]}... (first 20 chars)")
            else:
                print("✓ APP_SECRET_KEY is already configured")
    else:
        # Create .env from env.example
        if os.path.exists(env_example_path):
            print(f"Creating {env_path} from {env_example_path}...")
            
            with open(env_example_path, 'r') as f:
                content = f.read()
            
            # Generate secure secret key
            secret_key = generate_secret_key()
            
            # Replace the placeholder
            content = content.replace(
                'change_me_to_random_secret_key_minimum_32_characters',
                secret_key
            )
            
            with open(env_path, 'w') as f:
                f.write(content)
            
            print(f"✓ Created {env_path} with secure secret key")
            print(f"  Key: {secret_key[:20]}... (first 20 chars)")
        else:
            print(f"✗ Error: {env_example_path} not found")
            return False
    
    return True

def main():
    print("=" * 60)
    print("LLM Duel Arena - Authentication Setup")
    print("=" * 60)
    print()
    
    if not setup_env_file():
        return
    
    print()
    print("Next steps:")
    print("-" * 60)
    print("1. ✓ Secret key configured")
    print()
    print("2. [OPTIONAL] Set up Google OAuth:")
    print("   - Go to: https://console.cloud.google.com/apis/credentials")
    print("   - Create OAuth client ID")
    print("   - Add redirect URI: http://localhost:8000/auth/callback")
    print("   - Copy Client ID and Secret to .env file:")
    print("     GOOGLE_CLIENT_ID=your_client_id")
    print("     GOOGLE_CLIENT_SECRET=your_client_secret")
    print()
    print("3. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Start the server:")
    print("   uvicorn app.main:app --reload")
    print()
    print("5. Open: http://localhost:8000")
    print()
    print("=" * 60)
    print("ℹ️  Note: Authentication works without Google OAuth,")
    print("   but games won't be saved to user accounts.")
    print("=" * 60)

if __name__ == "__main__":
    main()








