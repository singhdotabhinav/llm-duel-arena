# AWS Cognito Authentication Setup Guide

This guide walks you through setting up AWS Cognito authentication for the LLM Duel Arena application.

## Module 1: AWS Cognito Setup

### Step 1: Create Cognito User Pool

1. **Navigate to AWS Console**
   - Go to AWS Cognito service
   - Click "Create user pool"

2. **Configure Sign-in Experience**
   - Choose "Email" as the sign-in option
   - Click "Next"

3. **Configure Security Requirements**
   - **Password policy**: Choose your requirements (minimum 8 characters recommended)
   - **Multi-Factor Authentication**: Optional but recommended
     - If enabled, choose "Authenticator app" or "SMS text message"
   - **User account recovery**: Enable "Email" for password reset
   - Click "Next"

4. **Configure Sign-up Experience**
   - **Self-service sign-up**: Enable
   - **Cognito-assisted verification**: Enable email verification
   - **Required attributes**: Select "email" and optionally "name"
   - Click "Next"

5. **Configure Message Delivery**
   - **Email provider**: Choose "Send email with Cognito"
   - Configure email settings
   - Click "Next"

6. **Integrate Your App**
   - **User pool name**: `llm-duel-arena-pool` (or your preferred name)
   - **App client name**: `llm-duel-arena-client`
   - **Client secret**: **Uncheck** "Generate client secret" (required for web apps)
   - Click "Next"

7. **Review and Create**
   - Review all settings
   - Click "Create user pool"

### Step 2: Configure App Client Settings

1. **Go to App Integration Tab**
   - Click on your user pool
   - Navigate to "App integration" tab

2. **Configure App Client**
   - Click on your app client
   - Under "Hosted UI", configure:
     - **Allowed callback URLs**: 
       - `http://localhost:8000/auth/callback` (for local dev)
       - `https://yourdomain.com/auth/callback` (for production)
     - **Allowed sign-out URLs**:
       - `http://localhost:8000/` (for local dev)
       - `https://yourdomain.com/` (for production)
     - **Allowed OAuth flows**: Check "Authorization code grant"
     - **Allowed OAuth scopes**: Check "openid", "email", "profile"
   - Click "Save changes"

### Step 3: Configure Domain (Optional - for Hosted UI)

1. **Go to Domain Tab**
   - Click "Create Cognito domain"
   - Choose a domain prefix (e.g., `llm-duel-arena`)
   - Click "Create Cognito domain"

### Step 4: Note Down Configuration Values

After setup, note down these values:

- **User Pool ID**: Found in "General settings" → "User pool ID"
- **App Client ID**: Found in "App integration" → "App client" → "Client ID"
- **Region**: Your AWS region (e.g., `us-east-1`)
- **Domain**: If using Hosted UI (e.g., `llm-duel-arena.auth.us-east-1.amazoncognito.com`)

## Module 2: Environment Configuration

### Step 1: Update .env File

Add the following to your `.env` file:

```bash
# AWS Cognito Configuration
USE_COGNITO=true
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_REGION=us-east-1
COGNITO_DOMAIN=llm-duel-arena  # Optional, for Hosted UI
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/

# AWS Credentials (for backend operations)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `boto3` - AWS SDK for Python
- `PyJWT` - JWT token verification
- `cryptography` - Cryptographic functions
- `requests` - HTTP requests

## Module 3: Frontend Integration

### Step 1: Update HTML Templates

The application will automatically use Cognito auth when `USE_COGNITO=true`.

### Step 2: Create Signup/Login Pages (Optional)

You can create custom signup/login pages or use the API endpoints directly:

- **Signup**: `POST /api/auth/signup`
- **Confirm Signup**: `POST /api/auth/confirm-signup`
- **Login**: `POST /api/auth/login`
- **Logout**: `GET /api/auth/logout`

### Step 3: Update Frontend JavaScript

The `cognito_auth.js` file provides helper functions:

```javascript
// Sign up
await window.cognitoAuth.signUp(email, password, name);

// Confirm signup
await window.cognitoAuth.confirmSignUp(email, confirmationCode);

// Login
await window.cognitoAuth.login(email, password);

// Logout
await window.cognitoAuth.logout();

// Check auth status
const authData = await window.cognitoAuth.checkAuth();
```

## Module 4: Backend Integration

### Step 1: Update Main Application

The application automatically switches to Cognito auth when configured:

```python
# In app/main.py
if settings.use_cognito:
    from .routers import cognito_auth
    app.include_router(cognito_auth.router, prefix="/auth", tags=["auth"])
else:
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

### Step 2: Protected Routes

Use the `get_current_user` dependency in your routes:

```python
from ..routers.cognito_auth import get_current_user

@router.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"message": f"Hello {user.email}"}
```

## Module 5: Security & Best Practices

### 1. HTTPS Configuration

- **Local Development**: HTTP is fine
- **Production**: Always use HTTPS
  - Set `secure=True` in cookie settings
  - Use HTTPS URLs for callbacks

### 2. Token Storage

- **Access Tokens**: Stored in HTTP-only cookies (server-side) or localStorage (client-side)
- **Refresh Tokens**: Stored securely, never expose in URLs
- **Token Expiry**: Access tokens expire in 1 hour (default), refresh automatically

### 3. Password Policy

Configure strong password requirements in Cognito:
- Minimum 8 characters
- Require uppercase, lowercase, numbers, symbols
- Prevent common passwords

### 4. Account Recovery

- Enable email-based password reset
- Configure account recovery questions (optional)

### 5. Monitoring

- Enable CloudWatch logging for Cognito
- Monitor sign-in attempts
- Set up alerts for suspicious activity

## Module 6: Testing

### Test Signup Flow

1. **Sign Up**
   ```bash
   curl -X POST http://localhost:8000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "Test123!@#", "name": "Test User"}'
   ```

2. **Check Email** for confirmation code

3. **Confirm Signup**
   ```bash
   curl -X POST http://localhost:8000/api/auth/confirm-signup \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "confirmation_code": "123456"}'
   ```

4. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "Test123!@#"}'
   ```

### Test Frontend Integration

1. Open browser console
2. Test signup:
   ```javascript
   await window.cognitoAuth.signUp('test@example.com', 'Test123!@#', 'Test User');
   ```

3. Test login:
   ```javascript
   await window.cognitoAuth.login('test@example.com', 'Test123!@#');
   ```

4. Check auth status:
   ```javascript
   await window.cognitoAuth.checkAuth();
   ```

## Troubleshooting

### Common Issues

1. **"Cognito is not enabled"**
   - Check `USE_COGNITO=true` in `.env`
   - Restart the application

2. **"Invalid client ID"**
   - Verify `COGNITO_CLIENT_ID` matches your app client ID
   - Ensure client secret is NOT enabled

3. **"User already exists"**
   - User is already registered
   - Use login endpoint instead

4. **"UserNotConfirmedException"**
   - User needs to confirm email
   - Check email for confirmation code

5. **Token Verification Fails**
   - Check `COGNITO_USER_POOL_ID` is correct
   - Verify `COGNITO_REGION` matches your pool region
   - Ensure JWKS endpoint is accessible

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Google OAuth

To migrate from Google OAuth to Cognito:

1. Set up Cognito (follow Module 1)
2. Update `.env` with Cognito credentials
3. Set `USE_COGNITO=true`
4. Restart application
5. Existing users will need to sign up again with Cognito

## Next Steps

- [ ] Set up Cognito User Pool
- [ ] Configure environment variables
- [ ] Test signup/login flows
- [ ] Update frontend to use Cognito auth
- [ ] Deploy to production with HTTPS
- [ ] Set up monitoring and alerts

## Additional Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Boto3 Cognito Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp.html)
- [JWT.io](https://jwt.io/) - JWT token decoder

