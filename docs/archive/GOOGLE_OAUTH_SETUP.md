# Google OAuth Setup Guide

This guide explains how to set up Google OAuth for the LLM Duel Arena authentication system.

## Prerequisites

- Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter project name: "LLM Duel Arena" (or your preferred name)
5. Click "Create"

### 2. Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace account)
3. Click "Create"
4. Fill in the required fields:
   - **App name**: LLM Duel Arena
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On "Scopes" page, click "Add or Remove Scopes"
7. Add these scopes:
   - `openid`
   - `email`
   - `profile`
8. Click "Save and Continue"
9. Add test users (your email) if in testing mode
10. Click "Save and Continue"

### 4. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Fill in:
   - **Name**: LLM Duel Arena Web Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:8000` (for development)
     - `http://127.0.0.1:8000` (for development)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/callback`
     - `http://127.0.0.1:8000/auth/callback`
5. Click "Create"
6. **Copy the Client ID and Client Secret** - you'll need these!

### 5. Update Your .env File

1. Copy `env.example` to `.env` if you haven't already:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and update these values:
   ```env
   # Google OAuth
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
   ```

3. Also update the APP_SECRET_KEY to a random string (at least 32 characters):
   ```bash
   # On Linux/Mac:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Or use openssl:
   openssl rand -base64 32
   ```

### 6. Install Dependencies

Install the new authentication dependencies:

```bash
pip install -r requirements.txt
```

### 7. Run the Application

Start your server:

```bash
uvicorn app.main:app --reload
```

### 8. Test Authentication

1. Go to http://localhost:8000
2. You should see a "Sign in with Google" button in the header
3. Click it to test the OAuth flow
4. After signing in, you should see your name and profile picture
5. Try creating a game - it will be saved to your account
6. Click "My Games" to see only your games

## Database

The application automatically creates a SQLite database (`llm_duel_arena.db`) in the project root with two tables:
- `users`: Stores user information from Google
- `games`: Stores games with user association

## Production Deployment

For production deployment:

1. **Update OAuth Credentials**:
   - Add your production domain to "Authorized JavaScript origins"
   - Add your production callback URL to "Authorized redirect URIs"
   - Example: `https://yourdomain.com/auth/callback`

2. **Update .env**:
   ```env
   GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
   APP_SECRET_KEY=generate_a_new_strong_secret_key
   ```

3. **Use PostgreSQL** (recommended for production):
   ```env
   DATABASE_URL=postgresql://user:password@localhost/llm_duel_arena
   ```

4. **Publish OAuth App**:
   - In Google Cloud Console, go to OAuth consent screen
   - Click "Publish App" to allow any Google user to sign in
   - Note: This requires verification for sensitive scopes (we only use basic profile, so it's quick)

## Features

### For Users:
- ✅ Sign in with Google account
- ✅ All games automatically saved to your account
- ✅ View only your games on "My Games" page
- ✅ Profile picture and name displayed
- ✅ Persistent sessions (30 days)

### For Developers:
- ✅ User authentication with OAuth 2.0
- ✅ Database storage for users and games
- ✅ Session management
- ✅ Easy integration with existing game system
- ✅ Privacy-focused (only stores email, name, picture)

## Troubleshooting

### "OAuth error: invalid_request"
- Check that your redirect URI in `.env` matches exactly what's in Google Console
- Make sure you're accessing the app via the same URL (localhost vs 127.0.0.1)

### "Google OAuth is not configured"
- Make sure you've set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
- Restart your server after updating `.env`

### Can't see login button
- Check browser console for errors
- Make sure `/static/js/auth.js` is loading correctly
- Clear browser cache and reload

### Games not saving
- Check that the database file was created (`llm_duel_arena.db`)
- Check server logs for errors
- Make sure you're logged in when creating games

## Security Notes

- Never commit your `.env` file to version control
- Keep your `GOOGLE_CLIENT_SECRET` private
- Use HTTPS in production
- The `APP_SECRET_KEY` should be unique and random
- Sessions are stored in memory (use Redis in production for scalability)

## Next Steps

- Add password reset functionality (if needed)
- Implement social sharing of games
- Add leaderboards based on win/loss records
- Export game history
- Add friend system for private matches

