const logEl = document.getElementById('log');
const whiteSel = document.getElementById('white-model');
const blackSel = document.getElementById('black-model');
const boardEl = document.getElementById('board');
const gridEl = document.getElementById('board-grid');
const piecesEl = document.getElementById('pieces');
const startBtn = document.getElementById('start');
const resetBtn = document.getElementById('reset');
const pauseBtn = document.getElementById('pause');
const resumeBtn = document.getElementById('resume');
const capWhiteEl = document.getElementById('captured-white');
const capBlackEl = document.getElementById('captured-black');
const whiteCountEl = document.getElementById('white-count');
const blackCountEl = document.getElementById('black-count');
let currentGameId = null;
let pollTimer = null;
let lastRenderedPly = 0;
let lastFen = null;
let lastMoveUci = null;
let capturedByWhite = []; // black pieces captured
let capturedByBlack = []; // white pieces captured

const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

const UNICODE = {
  'P':'\u2659','N':'\u2658','B':'\u2657','R':'\u2656','Q':'\u2655','K':'\u2654',
  'p':'\u265F','n':'\u265E','b':'\u265D','r':'\u265C','q':'\u265B','k':'\u265A'
};
const NAME = { 'P':'pawn','N':'knight','B':'bishop','R':'rook','Q':'queen','K':'king',
               'p':'pawn','n':'knight','b':'bishop','r':'rook','q':'queen','k':'king'};

function setControls(state){
  if(state==='busy'){
    startBtn.disabled = true; resetBtn.disabled = true; pauseBtn.disabled = true; resumeBtn.disabled = true; return;
  }
  if(state==='idle'){
    startBtn.disabled = false; resetBtn.disabled = true; pauseBtn.disabled = true; resumeBtn.disabled = true; return;
  }
  if(state==='running'){
    startBtn.disabled = true; resetBtn.disabled = false; pauseBtn.disabled = false; resumeBtn.disabled = true; return;
  }
  if(state==='paused'){
    startBtn.disabled = true; resetBtn.disabled = false; pauseBtn.disabled = true; resumeBtn.disabled = false;
  }
}

function addLog(msg){ const li=document.createElement('li'); li.textContent=msg; logEl.prepend(li); }
function clearLog(){ logEl.innerHTML = ''; }

async function api(path, opts={}){
  const res = await fetch(`/api/games${path}`, { headers: {'Content-Type':'application/json'}, ...opts, });
  if(!res.ok){ throw new Error(`API ${res.status}`); }
  return await res.json();
}

function setupGrid(){
  // if already built, just update highlights
  if(gridEl.childElementCount===64){
    const f = lastMoveUci?.slice(0,2); const t = lastMoveUci?.slice(2,4);
    [...gridEl.children].forEach(sq=>{
      sq.classList.remove('highlight');
      if(f && t){
        const here = `${sq.dataset.file}${sq.dataset.rank}`;
        if(here===f || here===t) sq.classList.add('highlight');
      }
    });
    return;
  }
  gridEl.innerHTML='';
  for(let r=0;r<8;r++){
    for(let c=0;c<8;c++){
      const sq=document.createElement('div');
      sq.className = `square ${(r+c)%2===0?'light':'dark'}`;
      const rank = String(8-r); const file = String.fromCharCode('a'.charCodeAt(0)+c);
      sq.dataset.rank = rank; sq.dataset.file = file;
      const label=document.createElement('span'); label.className='coord'; label.textContent=`${file}${rank}`; sq.appendChild(label);
      gridEl.appendChild(sq);
    }
  }
}

function squareToXY(sq){ const file = sq.charCodeAt(0) - 'a'.charCodeAt(0); const rank = parseInt(sq[1],10); return {x:file,y:8-rank}; }

function fenToPieces(fen){
  const board = []; const placement = fen.split(' ')[0]; const rows = placement.split('/');
  for(let r=0;r<8;r++){
    const row = rows[r]; let c=0;
    for(const ch of row){ if(/[1-8]/.test(ch)){ const n = parseInt(ch,10); for(let i=0;i<n;i++) board.push({sq:null}); c+=n; } else { board.push({piece:ch}); c+=1; } }
  }
  const out = [];
  for(let i=0;i<64;i++){
    const file = String.fromCharCode('a'.charCodeAt(0) + (i%8)); const rank = 8 - Math.floor(i/8);
    const sq = `${file}${rank}`; const cell = board[i]; if(cell && cell.piece){ out.push({sq, piece: cell.piece}); }
  }
  return out;
}

function boardCellSize(){ const rect = boardEl.getBoundingClientRect(); return {cellW: rect.width/8, cellH: rect.height/8}; }

function renderPieces(fen){
  piecesEl.innerHTML=''; const {cellW,cellH}=boardCellSize(); const items = fenToPieces(fen);
  for(const it of items){
    const {x,y} = squareToXY(it.sq);
    const el=document.createElement('div'); el.className = `piece ${/[A-Z]/.test(it.piece)?'white':'black'}`;
    el.textContent = UNICODE[it.piece] || '';
    el.style.transform = `translate(${x*cellW + cellW*0.5 - 16}px, ${y*cellH + cellH*0.5 - 20}px)`;
    el.style.opacity = '1'; piecesEl.appendChild(el);
  }
}

function animateMove(prevFen, uci){
  if(!prevFen || !uci || uci.length<4) return; const from = uci.slice(0,2); const to = uci.slice(2,4);
  // Use glyph from prevFen at from-square
  const placement = prevFen.split(' ')[0];
  const items = fenToPieces(prevFen);
  const movingItem = items.find(i=>i.sq===from);
  if(!movingItem) return; const glyph = UNICODE[movingItem.piece] || '';
  const {cellW,cellH}=boardCellSize();
  const fromXY = squareToXY(from); const toXY = squareToXY(to);
  const ghost = document.createElement('div'); ghost.className = `piece ${/[A-Z]/.test(movingItem.piece)?'white':'black'}`; ghost.textContent = glyph;
  ghost.style.position='absolute'; ghost.style.transition='transform .28s ease';
  ghost.style.transform = `translate(${fromXY.x*cellW + cellW*0.5 - 16}px, ${fromXY.y*cellH + cellH*0.5 - 20}px)`; piecesEl.appendChild(ghost);
  requestAnimationFrame(()=>{ ghost.style.transform = `translate(${toXY.x*cellW + cellW*0.5 - 16}px, ${toXY.y*cellH + cellH*0.5 - 20}px)`; });
  setTimeout(()=>{ try{ piecesEl.removeChild(ghost); }catch{} }, 320);
}

function renderCapturedTrays(){
  const {cellW}=boardCellSize(); const size = Math.min(cellW*0.9, 48);
  capWhiteEl.style.setProperty('--capSize', `${size}px`);
  capBlackEl.style.setProperty('--capSize', `${size}px`);
  capWhiteEl.innerHTML = capturedByBlack.map(p=>`<span class="cap white">${UNICODE[p.toUpperCase()]}</span>`).join('');
  capBlackEl.innerHTML = capturedByWhite.map(p=>`<span class="cap black">${UNICODE[p.toLowerCase()]}</span>`).join('');
}

function updateCapturedFromServer(record){
  if(!record) return;
  if(record.captured_piece){
    // Server supplies lowercase for black, uppercase for white. Keep as given.
    const ch = record.captured_piece;
    if(record.side === 'white'){
      // white moved; captured black piece -> store lowercase
      capturedByWhite.push(ch.toLowerCase());
    } else {
      // black moved; captured white piece -> store uppercase
      capturedByBlack.push(ch.toUpperCase());
    }
    renderCapturedTrays();
  }
}

function pieceName(ch){ return NAME[ch] || NAME[ch && ch.toUpperCase()] || 'piece'; }
function squareName(sq){ return `${sq[0]}${sq[1]}`; }

function startPolling(){ stopPolling(); pollTimer = setInterval(async()=>{ if(!currentGameId) return; try{ const state = await api(`/${currentGameId}`); renderState(state); }catch(e){ console.error(e); addLog('Polling error'); } }, 1200); }
function stopPolling(){ if(pollTimer){ clearInterval(pollTimer); pollTimer = null; } }

function renderState(state){
  if(state.moves && state.moves.length){
    const newMoves = state.moves.filter(m => m.ply > lastRenderedPly).sort((a,b)=>a.ply-b.ply);
    for(const m of newMoves){
      const from = m.from_square || m.move_uci.slice(0,2);
      const to = m.to_square || m.move_uci.slice(2,4);
      const movingItems = fenToPieces(lastFen);
      const movingObj = movingItems.find(i=>i.sq===from);
      const moving = movingObj ? movingObj.piece : null;
      const sideName = m.side;
      const movingName = moving ? pieceName(moving) : 'piece';
      const capText = m.captured_piece ? ` capturing ${pieceName(m.captured_piece)} on ${squareName(to)}` : '';
      addLog(`Move #${m.ply}: ${sideName} ${movingName} ${squareName(from)} → ${squareName(to)}${capText}`);
      updateCapturedFromServer(m);
      animateMove(lastFen, m.move_uci);
      lastRenderedPly = Math.max(lastRenderedPly, m.ply); lastMoveUci = m.move_uci;
    }
  }
  setupGrid(); renderPieces(state.fen); lastFen = state.fen; renderCapturedTrays();
  const itemsNow = fenToPieces(state.fen); whiteCountEl.textContent = `White: ${itemsNow.filter(i=>/[A-Z]/.test(i.piece)).length}`; blackCountEl.textContent = `Black: ${itemsNow.filter(i=>/[a-z]/.test(i.piece)).length}`;
  if(state.over){ addLog(`Game over: ${state.result.status} ${state.result.result || ''}`); stopPolling(); setControls('idle'); }
}

window.addEventListener('resize', ()=>{ if(lastFen){ setupGrid(); renderPieces(lastFen); renderCapturedTrays(); } });

startBtn.addEventListener('click', async()=>{
  try{
    setControls('busy'); const body = {white_model:whiteSel.value, black_model:blackSel.value};
    const state = await api('/', {method:'POST', body: JSON.stringify(body)});
    currentGameId = state.game_id; lastRenderedPly = 0; lastFen = state.fen; lastMoveUci = null; capturedByWhite = []; capturedByBlack = [];
    capWhiteEl.innerHTML=''; capBlackEl.innerHTML=''; clearLog(); setupGrid(); renderPieces(state.fen); renderCapturedTrays();
    addLog(`Started game ${currentGameId}`); await api(`/${currentGameId}/start_autoplay`, {method:'POST', body: JSON.stringify(body)});
    addLog('Autoplay started'); startPolling(); setControls('running');
  }catch(e){ console.error(e); addLog('Failed to start'); setControls('idle'); }
});

resetBtn.addEventListener('click', async()=>{
  if(!currentGameId) return; try{ setControls('busy'); const state = await api(`/${currentGameId}/reset`, {method:'POST'});
    lastRenderedPly = 0; lastFen = state.fen; lastMoveUci = null; capturedByWhite = []; capturedByBlack = []; capWhiteEl.innerHTML=''; capBlackEl.innerHTML='';
    clearLog(); setupGrid(); renderPieces(state.fen); renderCapturedTrays(); addLog(`Reset game ${state.game_id}`); setControls('idle');
  }catch(e){ console.error(e); addLog('Failed to reset'); setControls('idle'); }
});

pauseBtn.addEventListener('click', async()=>{ if(!currentGameId) return; try{ setControls('busy'); await api(`/${currentGameId}/pause`, {method:'POST'}); addLog('Paused'); setControls('paused'); }catch(e){ console.error(e); addLog('Failed to pause'); setControls('running'); } });
resumeBtn.addEventListener('click', async()=>{ if(!currentGameId) return; try{ setControls('busy'); await api(`/${currentGameId}/resume`, {method:'POST'}); addLog('Resumed'); setControls('running'); }catch(e){ console.error(e); addLog('Failed to resume'); setControls('paused'); } });

// initialize UI on load: show board immediately with starting position
setControls('idle');
lastFen = START_FEN; setupGrid(); renderPieces(lastFen); renderCapturedTrays(); whiteCountEl.textContent='White: 16'; blackCountEl.textContent='Black: 16';
