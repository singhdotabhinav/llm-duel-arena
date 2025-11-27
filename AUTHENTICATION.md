# Authentication System

## Overview

The LLM Duel Arena includes a complete Google OAuth 2.0 authentication system that allows users to:
- Sign in with their Google account
- Automatically save all games to their profile
- View their personal game history
- Track their battle statistics

## Architecture

### Components

1. **Database Models** (`app/database.py`)
   - `User`: Stores user information (Google ID, email, name, picture)
   - `Game`: Stores game records with user association

2. **Authentication Routes** (`app/routers/auth.py`)
   - `/auth/login` - Initiates Google OAuth flow
   - `/auth/callback` - Handles OAuth callback and creates session
   - `/auth/logout` - Ends user session
   - `/auth/user` - API endpoint to get current user info

3. **Session Management**
   - Uses secure HTTP-only cookies
   - 30-day session duration
   - In-memory session store (can be upgraded to Redis for production)

4. **Game Integration** (`app/routers/games.py`)
   - Games automatically associate with logged-in users
   - Non-authenticated users can still play (games won't be saved)

### Security Features

- **HTTP-only cookies**: Prevents XSS attacks
- **SameSite=Lax**: CSRF protection
- **Secure session tokens**: 32-byte URL-safe random tokens
- **OAuth 2.0**: Industry-standard authentication

## Setup Instructions

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"
4. Create OAuth Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure the OAuth consent screen first
   - Choose application type: "Web application"
   - Name it: "LLM Duel Arena" (or your preferred name)
5. Configure authorized redirect URIs:
   - **Development**: `http://localhost:8000/auth/callback`
   - **Production**: `https://yourdomain.com/auth/callback`
6. Copy the Client ID and Client Secret

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Required: Generate a random secret key
APP_SECRET_KEY=your_random_secret_key_at_least_32_characters_long

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_client_id_from_google_console
GOOGLE_CLIENT_SECRET=your_client_secret_from_google_console
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Database (SQLite by default)
DATABASE_URL=sqlite:///./llm_duel_arena.db
```

### 3. Restart the Server

```bash
uvicorn app.main:app --reload
```

The authentication system will be automatically activated!

## User Flow

### First-time User

1. User clicks "Sign in with Google" on the landing page
2. Redirected to Google's OAuth consent screen
3. After approval, redirected back to the app with auth code
4. Backend exchanges auth code for user info
5. New user account created in database
6. Session cookie set, user logged in
7. Redirected to home page with user info displayed

### Returning User

1. User clicks "Sign in with Google"
2. Google recognizes existing consent, immediately redirects back
3. User info updated (name, picture)
4. `last_login` timestamp updated
5. Session created, user logged in

### Creating Games

When logged in:
- Games automatically associate with user ID
- Saved to database on creation and after each move
- Accessible via "My Games" page

When not logged in:
- Games still playable
- Not saved to database
- Visible in "View Battles" (in-memory, temporary)

## API Endpoints

### Public Endpoints

```
GET  /auth/login          - Initiate Google OAuth
GET  /auth/callback       - OAuth callback handler
GET  /auth/logout         - Logout user
GET  /auth/user           - Get current user info (JSON)
```

### Protected Endpoints

```
GET  /api/games/my-games  - Get user's game history (requires login)
```

### Game Endpoints (Auto-save if logged in)

```
POST /api/games/random_duel       - Create random game
POST /api/games/                  - Create custom game
POST /api/games/{id}/move         - Make a move
POST /api/games/{id}/start_autoplay - Start AI vs AI
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Google user ID (sub claim) |
| email | String (unique) | User's email address |
| name | String | User's full name |
| picture | String | Profile picture URL |
| created_at | DateTime | Account creation timestamp |
| last_login | DateTime | Last login timestamp |

### Games Table

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Game ID (UUID) |
| user_id | String (FK) | Owner's user ID (nullable) |
| game_type | String | Type of game (chess, racing, etc.) |
| white_model | String | White player model |
| black_model | String | Black player model |
| result | String | Game result string |
| winner | String | Winner (white/black/draw) |
| moves_count | Integer | Number of moves played |
| is_over | Integer | Game finished flag (0/1) |
| created_at | DateTime | Game creation time |
| updated_at | DateTime | Last update time |
| game_state | Text (JSON) | Full game state and moves |

## Frontend Integration

### Auth UI Components

The landing page includes:
- **Login button**: Shown when not authenticated
- **User info**: Name and profile picture when logged in
- **My Games link**: Access personal game history
- **Logout button**: End session

### JavaScript (auth.js)

```javascript
// Check authentication status
const authData = await checkAuth();

// Update UI based on auth state
updateAuthUI(authData);

// Auth data structure
{
  logged_in: boolean,
  user: {
    id: string,
    email: string,
    name: string,
    picture: string
  }
}
```

### My Games Page

Accessible at `/my-games`:
- Lists all games played by the logged-in user
- Shows game type, models, status, and moves
- Links to view each game
- Automatically redirects to login if not authenticated

## Production Deployment

### Security Enhancements

1. **Use HTTPS**:
   ```python
   # Update redirect URI
   GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
   ```

2. **Set secure cookie flag**:
   ```python
   response.set_cookie(
       key="session_id",
       value=session_id,
       httponly=True,
       secure=True,  # HTTPS only
       samesite="lax"
   )
   ```

3. **Use Redis for sessions**:
   ```python
   # Instead of in-memory dict
   import redis
   redis_client = redis.from_url(os.getenv("REDIS_URL"))
   ```

4. **Database**:
   - Switch from SQLite to PostgreSQL for better concurrency
   - Configure `DATABASE_URL` in environment

### OAuth Consent Screen

For production, configure the OAuth consent screen:
- **App name**: Your application name
- **App logo**: Your app's logo
- **Support email**: Your support email
- **App domain**: Your website domain
- **Authorized domains**: Your production domain
- **Privacy Policy URL**: Link to privacy policy
- **Terms of Service URL**: Link to terms

### Rate Limiting

Consider adding rate limiting to auth endpoints:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...
```

## Troubleshooting

### "OAuth is not configured" Error

**Problem**: Google OAuth credentials not set

**Solution**: 
1. Check `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
2. Restart the server after adding credentials

### "redirect_uri_mismatch" Error

**Problem**: Redirect URI doesn't match Google Console configuration

**Solution**:
1. Check Google Console → OAuth client → Authorized redirect URIs
2. Ensure URI exactly matches (including http/https, port, path)
3. Common correct URIs:
   - Dev: `http://localhost:8000/auth/callback`
   - Prod: `https://yourdomain.com/auth/callback`

### Session Not Persisting

**Problem**: User gets logged out immediately

**Solution**:
1. Check browser accepts cookies
2. Verify `APP_SECRET_KEY` is set in `.env`
3. Check session isn't being cleared server-side

### Games Not Saving

**Problem**: Games don't appear in "My Games"

**Solution**:
1. Verify user is actually logged in (check `/auth/user` endpoint)
2. Check database file exists and is writable
3. Verify `save_game_to_db` is being called in game routes

## Future Enhancements

Potential improvements:
- **Email verification**: Verify email addresses before allowing sign-in
- **Multi-provider auth**: Add GitHub, Discord, etc.
- **User profiles**: Allow users to customize their profiles
- **Social features**: Friend lists, challenges, leaderboards
- **OAuth scopes**: Request only necessary permissions
- **Account deletion**: GDPR-compliant account deletion
- **2FA**: Two-factor authentication for enhanced security















