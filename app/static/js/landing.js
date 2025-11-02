// Landing page animations and interactions

document.addEventListener('DOMContentLoaded', () => {
  // Add sparkle effect on hover for buttons
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach(btn => {
    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'translateY(-3px) scale(1.05)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'translateY(0) scale(1)';
    });
  });

  // Random glow effect on fighters
  const fighters = document.querySelectorAll('.ai-fighter');
  setInterval(() => {
    fighters.forEach(fighter => {
      if (Math.random() > 0.7) {
        fighter.style.boxShadow = '0 0 30px rgba(0, 255, 255, 0.8)';
        setTimeout(() => {
          fighter.style.boxShadow = '';
        }, 500);
      }
    });
  }, 2000);

  // Parallax effect on scroll (if needed)
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    const stars = document.querySelectorAll('.stars, .stars2, .stars3');
    
    stars.forEach((star, index) => {
      const speed = (index + 1) * 0.5;
      star.style.transform = `translateY(${currentScroll * speed}px)`;
    });
    
    lastScroll = currentScroll;
  });

  // Quick match button handler
  const quickMatchBtn = document.querySelector('.btn-primary');
  if (quickMatchBtn) {
    const btnText = quickMatchBtn.querySelector('.btn-text');
    const hrefAttr = quickMatchBtn.getAttribute('href');
    
    quickMatchBtn.addEventListener('click', async (e) => {
      // Only intercept if it's the Random Duel button (has href="/game" without game_id)
      if (hrefAttr === '/game' || (hrefAttr && hrefAttr.startsWith('/game') && !hrefAttr.includes('game_id='))) {
        e.preventDefault();
        e.stopPropagation();
        
        if (btnText) {
          btnText.textContent = 'Starting...';
        }
        quickMatchBtn.style.pointerEvents = 'none';
        quickMatchBtn.style.opacity = '0.7';
        
        try {
          const res = await fetch('/api/games/random_duel', { method: 'POST' });
          if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`HTTP ${res.status}: ${errorText}`);
          }
          const data = await res.json();
          if (data.game_id) {
            window.location.href = `/game?game_id=${data.game_id}`;
          } else {
            throw new Error('No game_id in response');
          }
        } catch (error) {
          console.error('Failed to start random duel:', error);
          if (btnText) {
            btnText.textContent = 'Start Random Duel';
          }
          quickMatchBtn.style.pointerEvents = 'auto';
          quickMatchBtn.style.opacity = '1';
          alert('Failed to start duel: ' + error.message);
        }
      }
      // If it's "View Battles", let it navigate normally (href="/games")
    });
  }
  
  // Ensure all buttons are clickable
  document.querySelectorAll('.btn').forEach(btn => {
    btn.style.cursor = 'pointer';
  });

  // Animate feature cards on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'slideUp 0.8s ease-out forwards';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.feature-card').forEach(card => {
    observer.observe(card);
  });
});

