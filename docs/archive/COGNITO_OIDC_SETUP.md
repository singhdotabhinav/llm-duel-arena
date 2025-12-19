# AWS Cognito OIDC Setup Guide (Using authlib)

This guide shows how to set up AWS Cognito authentication using the authlib library with OIDC (OpenID Connect) flow, similar to the Flask example provided.

## Prerequisites

- AWS Account with Cognito access
- Python 3.8+
- FastAPI application

## Step 1: Configure Cognito User Pool

1. **Create User Pool in AWS Console**
   - Go to AWS Cognito → User Pools → Create user pool
   - Choose "Email" as sign-in option
   - Configure password policy
   - Enable self-service sign-up
   - Configure email verification

2. **Create App Client**
   - Go to "App integration" tab
   - Create app client
   - **Important**: For web apps, **DO NOT** generate client secret (uncheck the option)
   - Note down the **Client ID**

3. **Configure App Client Settings**
   - Under "Hosted UI", configure:
     - **Allowed callback URLs**: 
       - `http://localhost:8000/auth/callback` (local)
       - `https://yourdomain.com/auth/callback` (production)
     - **Allowed sign-out URLs**:
       - `http://localhost:8000/` (local)
       - `https://yourdomain.com/` (production)
     - **Allowed OAuth flows**: Check "Authorization code grant"
     - **Allowed OAuth scopes**: Check "openid", "email", "profile"

4. **Note Down Configuration Values**
   - **User Pool ID**: Found in "General settings" (e.g., `eu-north-1_6WUbLC1KS`)
   - **Client ID**: Found in "App integration" → App client (e.g., `371gt7emopsic4tqut8o5s4qep`)
   - **Region**: Your AWS region (e.g., `eu-north-1`)
   - **Client Secret**: Only if you enabled it (usually not needed for web apps)

## Step 2: Install Dependencies

The required packages are already in `requirements.txt`:
- `authlib==1.3.0` - OAuth/OIDC library
- `werkzeug` - Already included with FastAPI dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Enable Cognito
USE_COGNITO=true

# Cognito Configuration (from Step 1)
COGNITO_USER_POOL_ID=eu-north-1_6WUbLC1KS
COGNITO_CLIENT_ID=371gt7emopsic4tqut8o5s4qep
COGNITO_CLIENT_SECRET=  # Leave empty if no client secret
COGNITO_REGION=eu-north-1
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/

# Session secret (for session middleware)
APP_SECRET_KEY=your-secret-key-here-change-in-production
```

## Step 4: Code Implementation

The code has been implemented in `app/routers/cognito_oidc_auth.py` following the Flask example pattern:

### Key Components:

1. **OAuth Registration** (similar to Flask example):
```python
oauth.register(
    name='cognito',
    authority='https://cognito-idp.eu-north-1.amazonaws.com/eu-north-1_6WUbLC1KS',
    client_id='371gt7emopsic4tqut8o5s4qep',
    client_secret='<client secret>',  # Optional
    server_metadata_url='https://cognito-idp.eu-north-1.amazonaws.com/eu-north-1_6WUbLC1KS/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
```

2. **Login Route** - Redirects to Cognito Hosted UI:
```python
@router.get("/login")
async def login(request: Request):
    redirect_uri = settings.cognito_callback_url
    return await oauth.cognito.authorize_redirect(request, redirect_uri)
```

3. **Callback Route** - Handles OAuth callback:
```python
@router.get("/callback")
async def authorize(request: Request, db: Session = Depends(get_db)):
    token = await oauth.cognito.authorize_access_token(request)
    user_info = token.get('userinfo')
    # Store user in session
    request.session['user'] = user_info
    return RedirectResponse(url="/", status_code=302)
```

4. **Logout Route** - Clears session:
```python
@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url="/", status_code=302)
```

## Step 5: Usage

### Start the Application

```bash
uvicorn app.main:app --reload
```

### Test the Flow

1. **Navigate to Login**
   - Go to `http://localhost:8000/`
   - Click "Sign In with Cognito"
   - You'll be redirected to Cognito Hosted UI

2. **Sign Up (if new user)**
   - Click "Sign up" on Cognito page
   - Enter email and password
   - Verify email with code sent

3. **Login**
   - Enter credentials on Cognito page
   - You'll be redirected back to your app
   - Session will contain user info

4. **Check User Info**
   - Visit `http://localhost:8000/auth/user`
   - Should return user information if logged in

5. **Logout**
   - Click logout button
   - Session cleared, redirected to home

## Differences from Flask Example

The FastAPI implementation adapts the Flask code:

1. **OAuth Initialization**:
   - Flask: `OAuth(app)` → FastAPI: `OAuth(config)` (no app parameter)

2. **Route Decorators**:
   - Flask: `@app.route('/login')` → FastAPI: `@router.get("/login")`

3. **Request Handling**:
   - Flask: Uses `request` from Flask → FastAPI: Uses `Request` from FastAPI
   - Both use `request.session` for session management

4. **Redirects**:
   - Flask: `redirect(url_for('index'))` → FastAPI: `RedirectResponse(url="/")`

5. **OAuth Methods**:
   - Same: `oauth.cognito.authorize_redirect()`
   - Same: `oauth.cognito.authorize_access_token()`

## Troubleshooting

### "Cognito is not enabled"
- Check `USE_COGNITO=true` in `.env`
- Restart the application

### "Cognito is not configured"
- Verify `COGNITO_USER_POOL_ID` and `COGNITO_CLIENT_ID` are set
- Check they match your AWS Cognito configuration

### "Invalid redirect URI"
- Ensure callback URL in `.env` matches the one configured in Cognito
- Check allowed callback URLs in Cognito App Client settings

### "Failed to get user info"
- Verify OAuth scopes include "openid email profile"
- Check that user pool allows these scopes

### Session not persisting
- Ensure `APP_SECRET_KEY` is set in `.env`
- Check that SessionMiddleware is configured in `main.py`

## Production Deployment

1. **Use HTTPS**:
   - Update `COGNITO_CALLBACK_URL` to HTTPS URL
   - Set `https_only=True` in SessionMiddleware

2. **Secure Secret Key**:
   - Use a strong random secret for `APP_SECRET_KEY`
   - Store in environment variables or secrets manager

3. **Update Callback URLs**:
   - Add production callback URL to Cognito
   - Update `COGNITO_CALLBACK_URL` in production environment

4. **Session Storage**:
   - Consider using Redis for session storage in production
   - Current implementation uses in-memory sessions

## Additional Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [authlib Documentation](https://docs.authlib.org/)
- [FastAPI Sessions](https://fastapi.tiangolo.com/advanced/middleware/#using-httpx)

