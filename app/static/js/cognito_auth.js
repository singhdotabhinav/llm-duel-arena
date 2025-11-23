/**
 * AWS Cognito Authentication Client
 * Handles signup, login, token management, and user state
 */

// Store tokens in localStorage
const TOKEN_KEY = 'cognito_access_token';
const REFRESH_TOKEN_KEY = 'cognito_refresh_token';
const ID_TOKEN_KEY = 'cognito_id_token';

/**
 * Get API URL helper
 */
function getApiUrl(path) {
  return window.getApiUrl ? window.getApiUrl(path) : path;
}

/**
 * Store authentication tokens
 */
function storeTokens(accessToken, refreshToken, idToken) {
  if (accessToken) localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  if (idToken) localStorage.setItem(ID_TOKEN_KEY, idToken);
}

/**
 * Clear authentication tokens
 */
function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(ID_TOKEN_KEY);
}

/**
 * Get stored access token
 */
function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored refresh token
 */
function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Sign up a new user
 */
async function signUp(email, password, name = null) {
  try {
    const response = await fetch(getApiUrl('/api/auth/signup'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Signup failed');
    }

    return data;
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

/**
 * Confirm signup with verification code
 */
async function confirmSignUp(email, confirmationCode) {
  try {
    const response = await fetch(getApiUrl('/api/auth/confirm-signup'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, confirmation_code: confirmationCode }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Confirmation failed');
    }

    return data;
  } catch (error) {
    console.error('Confirm signup error:', error);
    throw error;
  }
}

/**
 * Login user
 */
async function login(email, password) {
  try {
    const response = await fetch(getApiUrl('/api/auth/login'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
      credentials: 'include', // Include cookies
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    // Store tokens
    if (data.access_token) {
      storeTokens(data.access_token, data.refresh_token, data.id_token);
    }

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

/**
 * Refresh access token
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(getApiUrl('/api/auth/refresh-token'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include',
    });

    const data = await response.json();
    
    if (!response.ok) {
      clearTokens();
      return null;
    }

    // Update stored tokens
    if (data.access_token) {
      storeTokens(data.access_token, refreshToken, data.id_token);
    }

    return data.access_token;
  } catch (error) {
    console.error('Token refresh error:', error);
    clearTokens();
    return null;
  }
}

/**
 * Logout user
 */
async function logout() {
  try {
    await fetch(getApiUrl('/api/auth/logout'), {
      method: 'GET',
      credentials: 'include',
    });
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearTokens();
    window.location.href = '/';
  }
}

/**
 * Check authentication status
 */
async function checkAuth() {
  try {
    const token = getAccessToken();
    if (!token) {
      return { logged_in: false };
    }

    const response = await fetch(getApiUrl('/api/auth/user'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    });

    const data = await response.json();
    
    // If token expired, try to refresh
    if (!data.logged_in && response.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        // Retry with new token
        const retryResponse = await fetch(getApiUrl('/api/auth/user'), {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${newToken}`,
          },
          credentials: 'include',
        });
        return await retryResponse.json();
      }
    }

    return data;
  } catch (error) {
    console.error('Auth check error:', error);
    return { logged_in: false };
  }
}

/**
 * Forgot password
 */
async function forgotPassword(email) {
  try {
    const response = await fetch(getApiUrl('/api/auth/forgot-password'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to initiate password reset');
    }

    return data;
  } catch (error) {
    console.error('Forgot password error:', error);
    throw error;
  }
}

/**
 * Confirm forgot password
 */
async function confirmForgotPassword(email, confirmationCode, newPassword) {
  try {
    const response = await fetch(getApiUrl('/api/auth/confirm-forgot-password'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        confirmation_code: confirmationCode,
        new_password: newPassword,
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Password reset failed');
    }

    return data;
  } catch (error) {
    console.error('Confirm forgot password error:', error);
    throw error;
  }
}

/**
 * Update auth UI based on authentication state
 */
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
  const authData = await checkAuth();
  updateAuthUI(authData);
});

// Export functions for use in other scripts
window.cognitoAuth = {
  signUp,
  confirmSignUp,
  login,
  logout,
  checkAuth,
  forgotPassword,
  confirmForgotPassword,
  getAccessToken,
  refreshAccessToken,
  updateAuthUI,
};

