// Authentication utility
// Supports both Google OAuth and AWS Cognito

// Check if Cognito auth is enabled (check for cognito_auth.js or use_cognito flag)
const USE_COGNITO = typeof window.cognitoAuth !== 'undefined' || 
                     (document.querySelector('meta[name="use-cognito"]')?.content === 'true');

async function checkAuth() {
  try {
    // Always use the /auth/user endpoint for Cognito OIDC (session-based)
    // This works for both Google OAuth and Cognito OIDC
    const url = window.getApiUrl ? window.getApiUrl('/auth/user') : '/auth/user';
    const res = await fetch(url, {
      credentials: 'include' // Include cookies for session-based auth
    });
    
    if (!res.ok) {
      return { logged_in: false };
    }
    
    const data = await res.json();
    return data;
  } catch (e) {
    console.error('Auth check failed:', e);
    return { logged_in: false };
  }
}

function updateAuthUI(authData) {
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const userInfo = document.getElementById('user-info');
  const userName = document.getElementById('user-name');
  const userAvatar = document.getElementById('user-avatar');
  
  if (authData.logged_in && authData.user) {
    // Show user info, hide login
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
    if (userInfo) userInfo.style.display = 'flex';
    if (userName) userName.textContent = authData.user.name || authData.user.email;
    if (userAvatar && authData.user.picture) {
      userAvatar.src = authData.user.picture;
      userAvatar.style.display = 'block';
    }
  } else {
    // Show login, hide user info
    if (loginBtn) loginBtn.style.display = 'inline-block';
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (userInfo) userInfo.style.display = 'none';
  }
}

// Auto-check auth on page load
document.addEventListener('DOMContentLoaded', async () => {
  // Show login button immediately (will be hidden if logged in)
  const loginBtn = document.getElementById('login-btn');
  if (loginBtn) {
    loginBtn.style.display = 'inline-block';
  }
  
  // Then check auth status and update UI
  try {
  const authData = await checkAuth();
  updateAuthUI(authData);
  } catch (error) {
    console.error('Failed to check auth:', error);
    // Ensure login button is visible on error
    if (loginBtn) {
      loginBtn.style.display = 'inline-block';
    }
  }
});

