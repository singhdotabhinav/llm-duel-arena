const logEl = document.getElementById('log');
const startBtn = document.getElementById('start');
const resetBtn = document.getElementById('reset');
const pauseBtn = document.getElementById('pause');
const resumeBtn = document.getElementById('resume');
const whiteSel = document.getElementById('white-model');
const blackSel = document.getElementById('black-model');

let currentGameId = null;
let pollTimer = null;
let countdownTimer = null;
let activeDeadline = null;
let lastRenderedPly = 0;
let hasAnnouncedGameOver = false;
const currentGameType = 'word_association_clash';

function setControls(state) {
  const modelSelector = document.getElementById('model-selector');
  const modelDisplay = document.getElementById('model-display');
  const whiteDisplay = document.getElementById('white-display');
  const blackDisplay = document.getElementById('black-display');

  if (state === 'busy') {
    startBtn.disabled = true;
    resetBtn.disabled = true;
    pauseBtn.disabled = true;
    resumeBtn.disabled = true;
    return;
  }

  if (state === 'idle') {
    startBtn.disabled = false;
    resetBtn.disabled = true;
    pauseBtn.disabled = true;
    resumeBtn.disabled = true;
    if (modelSelector) modelSelector.style.display = 'flex';
    if (modelDisplay) modelDisplay.style.display = 'none';
    return;
  }

  if (state === 'running') {
    startBtn.disabled = true;
    resetBtn.disabled = false;
    pauseBtn.disabled = false;
    resumeBtn.disabled = true;
    if (modelSelector) modelSelector.style.display = 'none';
    if (modelDisplay) {
      modelDisplay.style.display = 'flex';
      if (whiteDisplay) whiteDisplay.textContent = whiteSel.value;
      if (blackDisplay) blackDisplay.textContent = blackSel.value;
    }
    return;
  }

  if (state === 'paused') {
    startBtn.disabled = true;
    resetBtn.disabled = false;
    pauseBtn.disabled = true;
    resumeBtn.disabled = false;
    if (modelSelector) modelSelector.style.display = 'none';
    if (modelDisplay) {
      modelDisplay.style.display = 'flex';
      if (whiteDisplay) whiteDisplay.textContent = whiteSel.value;
      if (blackDisplay) blackDisplay.textContent = blackSel.value;
    }
  }
}

function addLog(message) {
  const li = document.createElement('li');
  li.textContent = message;
  logEl.prepend(li);
}

function clearLog() {
  logEl.innerHTML = '';
}

async function api(path, opts = {}) {
  const url = window.getApiUrl ? window.getApiUrl(`/api/games${path}`) : `/api/games${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

function buildHistoryRow(sideEmoji, response, valid, reason) {
  const statusClass = valid === false ? 'invalid' : 'valid';
  const reasonText = valid === false && reason ? `<span class="history-reason">${reason}</span>` : '';
  return `
    <div class="history-row ${statusClass}">
      <span class="history-side">${sideEmoji}</span>
      <span class="history-text">${response || '—'}</span>
      ${reasonText}
    </div>
  `;
}

function renderHistory(history) {
  const list = document.getElementById('history-list');
  if (!list) return;
  list.innerHTML = '';

  history.forEach((entry) => {
    const li = document.createElement('li');
    li.className = 'history-entry';
    const round = entry.round ?? '?';
    const prompt = entry.prompt ?? 'Prompt';
    li.innerHTML = `
      <h4>Round ${round}: ${prompt}</h4>
      ${buildHistoryRow('⚪', entry.white, entry.white_valid, entry.white_reason)}
      ${buildHistoryRow('⚫', entry.black, entry.black_valid, entry.black_reason)}
    `;
    list.appendChild(li);
  });
}

function updateTokens(state) {
  const whiteTokensEl = document.getElementById('white-tokens');
  const blackTokensEl = document.getElementById('black-tokens');
  if (whiteTokensEl && typeof state.white_tokens === 'number') {
    whiteTokensEl.textContent = state.white_tokens.toLocaleString();
  }
  if (blackTokensEl && typeof state.black_tokens === 'number') {
    blackTokensEl.textContent = state.black_tokens.toLocaleString();
  }
}

function updateScores(scores) {
  const whiteScoreEl = document.getElementById('white-score');
  const blackScoreEl = document.getElementById('black-score');
  if (whiteScoreEl && scores) {
    whiteScoreEl.textContent = (scores.white ?? 0).toString();
  }
  if (blackScoreEl && scores) {
    blackScoreEl.textContent = (scores.black ?? 0).toString();
  }
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  activeDeadline = null;
  const timerEl = document.getElementById('turn-timer');
  if (timerEl) {
    timerEl.textContent = '--';
    timerEl.classList.remove('timer-warning', 'timer-expired');
  }
}

function tickCountdown() {
  const timerEl = document.getElementById('turn-timer');
  if (!timerEl) return;
  if (!activeDeadline) {
    timerEl.textContent = '--';
    timerEl.classList.remove('timer-warning', 'timer-expired');
    return;
  }

  const msRemaining = activeDeadline * 1000 - Date.now();
  const clamped = Math.max(msRemaining, 0);
  const seconds = clamped / 1000;
  timerEl.textContent = `${seconds.toFixed(1)}s`;

  timerEl.classList.remove('timer-warning', 'timer-expired');
  if (seconds <= 0) {
    timerEl.classList.add('timer-expired');
  } else if (seconds <= 3) {
    timerEl.classList.add('timer-warning');
  }
}

function syncCountdown(deadline) {
  if (!deadline) {
    stopCountdown();
    return;
  }
  activeDeadline = deadline;
  tickCountdown();
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
  countdownTimer = setInterval(tickCountdown, 200);
}

function updateStatusBanner(apiState, engineState) {
  const banner = document.getElementById('status-banner');
  if (!banner) return;

  if (apiState.over) {
    const result = apiState.result || {};
    const winner = result.winner
      ? result.winner === 'white'
        ? '⚪ White'
        : '⚫ Black'
      : 'No winner';
    // Show timeout message more prominently
    let reason = result.result || 'Game completed';
    if (engineState.failure_reason && engineState.failure_reason.toLowerCase().includes('timeout')) {
      const timedOutSide = engineState.failure_side === 'white' ? '⚪ White' : '⚫ Black';
      reason = `${timedOutSide} failed to respond in time - ${winner} wins!`;
    } else if (engineState.failure_reason) {
      reason = `Reason: ${engineState.failure_reason}`;
    }
    banner.textContent = `${winner} wins • ${reason}`;
    banner.classList.remove('status-waiting', 'status-warning');
    banner.classList.add('status-complete');
    banner.hidden = false;
    return;
  }

  if (engineState.failure_reason) {
    const side = engineState.failure_side === 'white' ? '⚪ White' : '⚫ Black';
    banner.textContent = `${side} violation • ${engineState.failure_reason}`;
    banner.classList.remove('status-waiting', 'status-complete');
    banner.classList.add('status-warning');
    banner.hidden = false;
    return;
  }

  if (!engineState.current_prompt) {
    banner.textContent = 'All prompts completed';
    banner.classList.remove('status-warning', 'status-complete');
    banner.classList.add('status-waiting');
    banner.hidden = false;
    return;
  }

  const waitingFor = engineState.turn === 'white' ? '⚪ White' : '⚫ Black';
  banner.textContent = `Awaiting ${waitingFor} response...`;
  banner.classList.remove('status-warning', 'status-complete');
  banner.classList.add('status-waiting');
  banner.hidden = false;
}

function renderAssociationState(state) {
  const engineState = state.state ? JSON.parse(state.state) : {};
  const roundInfoEl = document.getElementById('round-info');
  const promptEl = document.getElementById('current-prompt');
  const turnEl = document.getElementById('turn-indicator');

  if (roundInfoEl) {
    roundInfoEl.textContent = `Round ${engineState.current_round || 0} / ${engineState.max_rounds || 0}`;
  }
  if (promptEl) {
    promptEl.textContent = engineState.current_prompt || 'All prompts completed';
  }
  if (turnEl) {
    turnEl.textContent = engineState.turn || 'white';
  }

  updateTokens(state);
  updateScores(engineState.scores || { white: 0, black: 0 });
  renderHistory(engineState.history || []);
  updateStatusBanner(state, engineState);

  if (engineState.turn_deadline && !state.over) {
    syncCountdown(engineState.turn_deadline);
  } else if (state.over) {
    stopCountdown();
  }

  if (state.moves && state.moves.length) {
    const newMoves = state.moves
      .filter((m) => m.ply > lastRenderedPly)
      .sort((a, b) => a.ply - b.ply);
    for (const move of newMoves) {
      const sideName = move.side;
      const tokenText = move.tokens_used ? ` [${move.tokens_used} tokens]` : '';
      addLog(`Move #${move.ply}: ${sideName} → ${move.move_uci}${tokenText}`);
      lastRenderedPly = Math.max(lastRenderedPly, move.ply);
    }
  }

  if (state.over && !hasAnnouncedGameOver) {
    const result = state.result || {};
    const engineState = state.state ? JSON.parse(state.state) : {};
    
    // Check if game ended due to timeout
    if (engineState.failure_reason && engineState.failure_reason.toLowerCase().includes('timeout')) {
      const timedOutSide = engineState.failure_side === 'white' ? 'White' : 'Black';
      const winner = result.winner === 'white' ? 'White' : 'Black';
      addLog(`⏱️ Timeout! ${timedOutSide} failed to respond in time. ${winner} wins!`);
    } else {
    const winner = result.winner ? `${result.winner} wins` : result.result || 'Game over';
    addLog(`Game over: ${winner}`);
    }
    
    hasAnnouncedGameOver = true;
    stopPolling();
    stopCountdown();
    setControls('idle');
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(async () => {
    if (!currentGameId) return;
    try {
      const state = await api(`/${currentGameId}`);
      renderAssociationState(state);
    } catch (err) {
      console.error(err);
      addLog(`Polling error: ${err.message}`);
    }
  }, 1500);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

// Helper function to parse custom keywords
function parseCustomKeywords(keywordsText) {
  if (!keywordsText || !keywordsText.trim()) {
    return null; // Use defaults
  }
  
  // Split by newlines or commas, trim, and filter empty strings
  const keywords = keywordsText
    .split(/[\n,]+/)
    .map(k => k.trim())
    .filter(k => k.length > 0)
    .slice(0, 12); // Limit to 12 keywords (MAX_ROUNDS)
  
  return keywords.length > 0 ? keywords : null;
}

startBtn.addEventListener('click', async () => {
  try {
    setControls('busy');

    // Get custom keywords
    const keywordsTextarea = document.getElementById('custom-keywords');
    const customKeywords = parseCustomKeywords(keywordsTextarea?.value || '');
    
    // Prepare initial_state if custom keywords provided
    let initialState = null;
    if (customKeywords) {
      initialState = JSON.stringify({ custom_prompts: customKeywords });
      addLog(`Using ${customKeywords.length} custom keywords`);
    }

    if (currentGameId) {
      const currentState = await api(`/${currentGameId}`);
      if (currentState.over) {
        clearLog();
        lastRenderedPly = 0;
        hasAnnouncedGameOver = false;
        const body = {
          game_type: currentGameType,
          white_model: whiteSel.value,
          black_model: blackSel.value,
          initial_state: initialState,
        };
        const state = await api('/', { method: 'POST', body: JSON.stringify(body) });
        currentGameId = state.game_id;
        renderAssociationState(state);
        addLog(`Started ${currentGameType} game ${currentGameId}`);
        await api(`/${currentGameId}/start_autoplay`, { method: 'POST', body: JSON.stringify({ white_model: whiteSel.value, black_model: blackSel.value }) });
        addLog('Autoplay started');
        startPolling();
        setControls('running');
        return;
      }

      const body = { white_model: whiteSel.value, black_model: blackSel.value };
      await api(`/${currentGameId}/start_autoplay`, { method: 'POST', body: JSON.stringify(body) });
      addLog('Autoplay resumed');
      startPolling();
      setControls('running');
      return;
    }

    clearLog();
    lastRenderedPly = 0;
    hasAnnouncedGameOver = false;
    const body = {
      game_type: currentGameType,
      white_model: whiteSel.value,
      black_model: blackSel.value,
      initial_state: initialState,
    };
    const state = await api('/', { method: 'POST', body: JSON.stringify(body) });
    currentGameId = state.game_id;
    renderAssociationState(state);
    addLog(`Started ${currentGameType} game ${currentGameId}`);
    await api(`/${currentGameId}/start_autoplay`, { method: 'POST', body: JSON.stringify({ white_model: whiteSel.value, black_model: blackSel.value }) });
    addLog('Autoplay started');
    startPolling();
    setControls('running');
  } catch (err) {
    console.error(err);
    addLog(`Failed to start: ${err.message}`);
    setControls('idle');
  }
});

resetBtn.addEventListener('click', async () => {
  if (!currentGameId) return;
  try {
    setControls('busy');
    
    // Get custom keywords for reset
    const keywordsTextarea = document.getElementById('custom-keywords');
    const customKeywords = parseCustomKeywords(keywordsTextarea?.value || '');
    let initialState = null;
    if (customKeywords) {
      initialState = JSON.stringify({ custom_prompts: customKeywords });
    }
    
    // Reset with custom keywords if provided
    const resetBody = initialState ? { initial_state: initialState } : {};
    const state = await api(`/${currentGameId}/reset`, { 
      method: 'POST',
      body: JSON.stringify(resetBody)
    });
    clearLog();
    lastRenderedPly = 0;
    hasAnnouncedGameOver = false;
    stopCountdown();
    renderAssociationState(state);
    addLog(`Reset ${state.game_type} ${state.game_id}`);
    setControls('idle');
  } catch (err) {
    console.error(err);
    addLog(`Failed to reset: ${err.message}`);
    setControls('idle');
  }
});

pauseBtn.addEventListener('click', async () => {
  if (!currentGameId) return;
  try {
    setControls('busy');
    await api(`/${currentGameId}/pause`, { method: 'POST' });
    addLog('Paused');
    setControls('paused');
  } catch (err) {
    console.error(err);
    addLog(`Failed to pause: ${err.message}`);
    setControls('running');
  }
});

resumeBtn.addEventListener('click', async () => {
  if (!currentGameId) return;
  try {
    setControls('busy');
    await api(`/${currentGameId}/resume`, { method: 'POST' });
    addLog('Resumed');
    setControls('running');
  } catch (err) {
    console.error(err);
    addLog(`Failed to resume: ${err.message}`);
    setControls('paused');
  }
});

setControls('idle');

const urlParams = new URLSearchParams(window.location.search);
const existingGameId = urlParams.get('game_id');
if (existingGameId) {
  currentGameId = existingGameId;
  api(`/${existingGameId}`)
    .then((state) => {
      if (state.game_type === currentGameType) {
        lastRenderedPly = 0;
        hasAnnouncedGameOver = state.over;
        renderAssociationState(state);
        if (state.moves && state.moves.length) {
          lastRenderedPly = state.moves.length;
        }

        if (state.moves && state.moves.length > 0 && !state.over) {
          startPolling();
          setControls('running');
          addLog('Watching ongoing game...');
        } else {
          setControls('idle');
          addLog('Game loaded. Click Start to begin.');
        }
        if (state.white_model) whiteSel.value = state.white_model;
        if (state.black_model) blackSel.value = state.black_model;
      } else {
        setControls('idle');
      }
    })
    .catch((err) => {
      console.error('Failed to load game:', err);
      addLog(`Failed to load: ${err.message}`);
      setControls('idle');
    });
}





