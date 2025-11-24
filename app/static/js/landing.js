// Minimal landing page interactions

document.addEventListener('DOMContentLoaded', () => {
  // Game selector and start duel button
  const startDuelBtn = document.getElementById('start-duel-btn');
  const gameTypeSelect = document.getElementById('game-type');

  if (startDuelBtn && gameTypeSelect) {
    startDuelBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const gameType = gameTypeSelect.value;
      console.log('Selected game type:', gameType);

      const originalText = startDuelBtn.textContent;
      startDuelBtn.textContent = 'Starting...';
      startDuelBtn.disabled = true;
      startDuelBtn.style.opacity = '0.7';

      try {
        const payload = { game_type: gameType };
        console.log('Sending payload:', payload);

        const url = window.getApiUrl ? window.getApiUrl('/api/games/random_duel') : '/api/games/random_duel';
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`HTTP ${res.status}: ${errorText} `);
        }
        const data = await res.json();
        console.log('Response:', data);

        if (data.game_id) {
          window.location.href = `/ game ? game_id = ${data.game_id} `;
        } else {
          throw new Error('No game_id in response');
        }
      } catch (error) {
        console.error('Failed to start duel:', error);
        startDuelBtn.textContent = originalText;
        startDuelBtn.disabled = false;
        startDuelBtn.style.opacity = '1';
        alert('Failed to start duel: ' + error.message);
      }
    });
  }

  // Subtle parallax on scroll
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const scrolled = window.pageYOffset;
        const heroImage = document.querySelector('.hero-image');
        if (heroImage) {
          heroImage.style.transform = `translateY(${scrolled * 0.3}px)`;
        }
        ticking = false;
      });
      ticking = true;
    }
  });
});

