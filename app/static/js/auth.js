// Authentication utility
async function checkAuth() {
  try {
    const res = await fetch('/auth/user');
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
  const authData = await checkAuth();
  updateAuthUI(authData);
});

