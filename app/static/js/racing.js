const logEl = document.getElementById('log');
const whiteSel = document.getElementById('white-model');
const blackSel = document.getElementById('black-model');
const startBtn = document.getElementById('start');
const resetBtn = document.getElementById('reset');
const pauseBtn = document.getElementById('pause');
const resumeBtn = document.getElementById('resume');

const whiteVehicle = document.getElementById('white-vehicle');
const blackVehicle = document.getElementById('black-vehicle');
const whiteSpeedEl = document.getElementById('white-speed');
const blackSpeedEl = document.getElementById('black-speed');
const whitePositionEl = document.getElementById('white-position');
const blackPositionEl = document.getElementById('black-position');
const whiteMovesEl = document.getElementById('white-moves');
const blackMovesEl = document.getElementById('black-moves');

let currentGameId = null;
let pollTimer = null;
let lastRenderedPly = 0;

const TRACK_LENGTH = 100;
const MAX_MOVES = 20;

function setControls(state){
  const modelSelector = document.getElementById('model-selector');
  const modelDisplay = document.getElementById('model-display');
  const whiteDisplay = document.getElementById('white-display');
  const blackDisplay = document.getElementById('black-display');
  
  if(state==='busy'){
    startBtn.disabled = true; resetBtn.disabled = true; pauseBtn.disabled = true; resumeBtn.disabled = true; return;
  }
  if(state==='idle'){
    startBtn.disabled = false; resetBtn.disabled = true; pauseBtn.disabled = true; resumeBtn.disabled = true;
    if(modelSelector) modelSelector.style.display = 'flex';
    if(modelDisplay) modelDisplay.style.display = 'none';
    return;
  }
  if(state==='running'){
    startBtn.disabled = true; resetBtn.disabled = false; pauseBtn.disabled = false; resumeBtn.disabled = true;
    if(modelSelector) modelSelector.style.display = 'none';
    if(modelDisplay){
      modelDisplay.style.display = 'flex';
      if(whiteDisplay) whiteDisplay.textContent = whiteSel.value;
      if(blackDisplay) blackDisplay.textContent = blackSel.value;
    }
    return;
  }
  if(state==='paused'){
    startBtn.disabled = true; resetBtn.disabled = false; pauseBtn.disabled = true; resumeBtn.disabled = false;
    if(modelSelector) modelSelector.style.display = 'none';
    if(modelDisplay){
      modelDisplay.style.display = 'flex';
      if(whiteDisplay) whiteDisplay.textContent = whiteSel.value;
      if(blackDisplay) blackDisplay.textContent = blackSel.value;
    }
  }
}

function addLog(msg){ 
  const li=document.createElement('li'); 
  li.textContent=msg; 
  logEl.prepend(li); 
}

function clearLog(){ 
  logEl.innerHTML = ''; 
}

async function api(path, opts={}){
  const url = window.getApiUrl ? window.getApiUrl(`/api/games${path}`) : `/api/games${path}`;
  const res = await fetch(url, { headers: {'Content-Type':'application/json'}, ...opts, });
  if(!res.ok){ throw new Error(`API ${res.status}`); }
  return await res.json();
}

function parseRacingState(stateStr){
  // State format: "white_pos:white_speed:white_moves|black_pos:black_speed:black_moves|turn"
  try {
    const parts = stateStr.split('|');
    const whiteData = parts[0].split(':');
    const blackData = parts[1].split(':');
    
    return {
      whitePosition: parseInt(whiteData[0]) || 0,
      whiteSpeed: parseInt(whiteData[1]) || 0,
      whiteMoves: parseInt(whiteData[2]) || 0,
      blackPosition: parseInt(blackData[0]) || 0,
      blackSpeed: parseInt(blackData[1]) || 0,
      blackMoves: parseInt(blackData[2]) || 0,
      turn: parts[2] || 'white'
    };
  } catch(e) {
    return {
      whitePosition: 0, whiteSpeed: 0, whiteMoves: 0,
      blackPosition: 0, blackSpeed: 0, blackMoves: 0,
      turn: 'white'
    };
  }
}

function animateVehicle(vehicle, position, speed){
  // Calculate percentage along track (0-100%)
  const percentage = Math.min((position / TRACK_LENGTH) * 100, 100);
  
  // Animate position
  vehicle.style.transition = 'left 0.6s ease-out, transform 0.3s ease';
  vehicle.style.left = `${percentage}%`;
  
  // Add speed effect (scale and tilt) - scaleX(-1) flips the car to face right
  if(speed > 0){
    const scale = 1 + (speed * 0.03); // Bigger at higher speeds
    const tilt = Math.min(speed * 2, 15); // Tilt forward
    vehicle.style.transform = `translateX(-50%) scaleX(-1) scale(${scale}) rotateZ(-${tilt}deg)`;
    
    // Add speed lines effect
    if(speed >= 5){
      vehicle.classList.add('speed-boost');
    } else {
      vehicle.classList.remove('speed-boost');
    }
  } else {
    vehicle.style.transform = 'translateX(-50%) scaleX(-1) scale(1)';
    vehicle.classList.remove('speed-boost');
  }
}

function renderRacingState(state){
  const gameState = parseRacingState(state.state);
  
  // Update vehicle positions with animation
  animateVehicle(whiteVehicle, gameState.whitePosition, gameState.whiteSpeed);
  animateVehicle(blackVehicle, gameState.blackPosition, gameState.blackSpeed);
  
  // Update speed displays
  whiteSpeedEl.textContent = `Speed: ${gameState.whiteSpeed}`;
  blackSpeedEl.textContent = `Speed: ${gameState.blackSpeed}`;
  
  // Update position displays
  whitePositionEl.textContent = `Position: ${gameState.whitePosition}/${TRACK_LENGTH}`;
  blackPositionEl.textContent = `Position: ${gameState.blackPosition}/${TRACK_LENGTH}`;
  
  // Update move counters
  whiteMovesEl.textContent = `White Moves: ${gameState.whiteMoves}/${MAX_MOVES}`;
  blackMovesEl.textContent = `Black Moves: ${gameState.blackMoves}/${MAX_MOVES}`;
  
  // Update token counters
  const whiteTokensEl = document.getElementById('white-tokens');
  const blackTokensEl = document.getElementById('black-tokens');
  if(whiteTokensEl && state.white_tokens !== undefined){
    whiteTokensEl.textContent = state.white_tokens.toLocaleString();
  }
  if(blackTokensEl && state.black_tokens !== undefined){
    blackTokensEl.textContent = state.black_tokens.toLocaleString();
  }
  
  // Highlight current turn
  const whiteLane = document.querySelector('.white-lane');
  const blackLane = document.querySelector('.black-lane');
  if(gameState.turn === 'white'){
    whiteLane?.classList.add('active-lane');
    blackLane?.classList.remove('active-lane');
  } else {
    blackLane?.classList.add('active-lane');
    whiteLane?.classList.remove('active-lane');
  }
  
  // Process new moves
  if(state.moves && state.moves.length){
    const newMoves = state.moves.filter(m => m.ply > lastRenderedPly).sort((a,b)=>a.ply-b.ply);
    for(const m of newMoves){
      const action = m.move_uci;
      const side = m.side;
      let emoji = '';
      
      if(action === 'accelerate') emoji = '🚀';
      else if(action === 'boost') emoji = '⚡';
      else if(action === 'maintain') emoji = '🔄';
      
      const currentPos = side === 'white' ? gameState.whitePosition : gameState.blackPosition;
      const currentSpeed = side === 'white' ? gameState.whiteSpeed : gameState.blackSpeed;
      const tokenText = m.tokens_used ? ` [${m.tokens_used} tokens]` : '';
      
      addLog(`Move #${m.ply}: ${emoji} ${side.toUpperCase()} ${action} (Speed: ${currentSpeed}, Pos: ${currentPos})${tokenText}`);
      lastRenderedPly = Math.max(lastRenderedPly, m.ply);
      
      // Add celebration effect for finish
      if(currentPos >= TRACK_LENGTH){
        const vehicle = side === 'white' ? whiteVehicle : blackVehicle;
        vehicle.classList.add('finished');
        addLog(`🏆 ${side.toUpperCase()} CROSSED THE FINISH LINE! 🏆`);
      }
    }
  }
  
  // Check if game over
  if(state.over){
    const result = state.result;
    stopPolling();
    setControls('idle');
    
    // Victory animation
    if(result.winner === 'white'){
      whiteVehicle.classList.add('winner');
      addLog(`🎉 RACE OVER: White wins! ${result.result}`);
    } else if(result.winner === 'black'){
      blackVehicle.classList.add('winner');
      addLog(`🎉 RACE OVER: Black wins! ${result.result}`);
    } else {
      addLog(`🏁 RACE OVER: Draw! ${result.result}`);
    }
  }
}

function startPolling(){ 
  stopPolling(); 
  pollTimer = setInterval(async()=>{ 
    if(!currentGameId) return; 
    try{ 
      const state = await api(`/${currentGameId}`); 
      renderRacingState(state); 
    }catch(e){ 
      console.error(e); 
      addLog('Polling error'); 
    } 
  }, 800); // Faster polling for racing
}

function stopPolling(){ 
  if(pollTimer){ 
    clearInterval(pollTimer); 
    pollTimer = null; 
  } 
}

startBtn.addEventListener('click', async()=>{
  try{
    setControls('busy');
    
    if(currentGameId){
      const currentState = await api(`/${currentGameId}`);
      
      if(currentState.over){
        // Start new race
        clearLog();
        lastRenderedPly = 0;
        
        // Reset vehicle positions
        whiteVehicle.style.left = '0%';
        blackVehicle.style.left = '0%';
        whiteVehicle.classList.remove('finished', 'winner', 'speed-boost');
        blackVehicle.classList.remove('finished', 'winner', 'speed-boost');
        
        const body = {game_type: 'racing', white_model:whiteSel.value, black_model:blackSel.value};
        const state = await api('/', {method:'POST', body: JSON.stringify(body)});
        currentGameId = state.game_id;
        
        renderRacingState(state);
        addLog(`Started new racing game ${currentGameId}`);
        
        await api(`/${currentGameId}/start_autoplay`, {method:'POST', body: JSON.stringify(body)});
        addLog('🏁 Race started!');
        startPolling();
        setControls('running');
        return;
      }
      
      // Resume existing race
      const body = {white_model:whiteSel.value, black_model:blackSel.value};
      await api(`/${currentGameId}/start_autoplay`, {method:'POST', body: JSON.stringify(body)});
      addLog('Race resumed');
      startPolling();
      setControls('running');
      return;
    }
    
    // Create new race
    clearLog();
    lastRenderedPly = 0;
    
    // Reset vehicle positions
    whiteVehicle.style.left = '0%';
    blackVehicle.style.left = '0%';
    whiteVehicle.classList.remove('finished', 'winner', 'speed-boost');
    blackVehicle.classList.remove('finished', 'winner', 'speed-boost');
    
    const body = {game_type: 'racing', white_model:whiteSel.value, black_model:blackSel.value};
    const state = await api('/', {method:'POST', body: JSON.stringify(body)});
    currentGameId = state.game_id;
    
    renderRacingState(state);
    addLog(`Started racing game ${currentGameId}`);
    
    await api(`/${currentGameId}/start_autoplay`, {method:'POST', body: JSON.stringify(body)});
    addLog('🏁 Race started!');
    startPolling();
    setControls('running');
  }catch(e){ 
    console.error(e); 
    addLog('Failed to start race'); 
    setControls('idle'); 
  }
});

resetBtn.addEventListener('click', async()=>{
  if(!currentGameId) return;
  try{
    setControls('busy');
    stopPolling();
    
    const state = await api(`/${currentGameId}/reset`, {method:'POST'});
    lastRenderedPly = 0;
    
    // Reset vehicles
    whiteVehicle.style.left = '0%';
    blackVehicle.style.left = '0%';
    whiteVehicle.classList.remove('finished', 'winner', 'speed-boost');
    blackVehicle.classList.remove('finished', 'winner', 'speed-boost');
    
    clearLog();
    renderRacingState(state);
    addLog(`Reset race ${state.game_id}`);
    setControls('idle');
  }catch(e){
    console.error(e);
    addLog('Failed to reset');
    setControls('idle');
  }
});

pauseBtn.addEventListener('click', async()=>{
  if(!currentGameId) return;
  try{
    setControls('busy');
    await api(`/${currentGameId}/pause`, {method:'POST'});
    stopPolling();
    addLog('⏸️ Race paused');
    setControls('paused');
  }catch(e){
    console.error(e);
    addLog('Failed to pause');
    setControls('running');
  }
});

resumeBtn.addEventListener('click', async()=>{
  if(!currentGameId) return;
  try{
    setControls('busy');
    await api(`/${currentGameId}/resume`, {method:'POST'});
    addLog('▶️ Race resumed');
    startPolling();
    setControls('running');
  }catch(e){
    console.error(e);
    addLog('Failed to resume');
    setControls('paused');
  }
});

// Initialize UI
setControls('idle');
whiteVehicle.style.left = '0%';
blackVehicle.style.left = '0%';

// Check if loading existing game from URL
const urlParams = new URLSearchParams(window.location.search);
const existingGameId = urlParams.get('game_id');
if (existingGameId) {
  currentGameId = existingGameId;
  api(`/${existingGameId}`).then(state => {
    if(state.game_type === 'racing'){
      lastRenderedPly = 0;
      renderRacingState(state);
      
      // Log existing moves
      if(state.moves && state.moves.length){
        state.moves.forEach(m => {
          const action = m.move_uci;
          let emoji = action === 'accelerate' ? '🚀' : action === 'boost' ? '⚡' : '🔄';
          addLog(`Move #${m.ply}: ${emoji} ${m.side} ${action}`);
        });
        lastRenderedPly = state.moves.length;
      }
      
      // Set models
      if(state.white_model) whiteSel.value = state.white_model;
      if(state.black_model) blackSel.value = state.black_model;
      
      if(state.moves && state.moves.length > 0 && !state.over){
        startPolling();
        setControls('running');
        addLog('Watching ongoing race...');
      } else {
        setControls('idle');
        addLog('Race loaded. Click Start to begin.');
      }
    }
  }).catch(err => {
    console.error('Failed to load race:', err);
    setControls('idle');
  });
}

