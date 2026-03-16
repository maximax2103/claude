'use strict';

// ── Telegram WebApp init ──────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

function haptic(type = 'light') {
  tg?.HapticFeedback?.impactOccurred(type);
}

// ── Constants ─────────────────────────────────────────────────────────────────
const COLS = 10;
const ROWS = 20;
const CELL = 30; // px per cell on main board
const NEXT_CELL = 20;

const COLORS = [
  null,
  '#00cfcf', // I – cyan
  '#f5a623', // O – orange
  '#9b59b6', // T – purple
  '#27ae60', // S – green
  '#e74c3c', // Z – red
  '#2980b9', // J – blue
  '#e67e22', // L – dark-orange
];

const PIECES = [
  null,
  [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]], // I
  [[2,2],[2,2]],                               // O
  [[0,3,0],[3,3,3],[0,0,0]],                   // T
  [[0,4,4],[4,4,0],[0,0,0]],                   // S
  [[5,5,0],[0,5,5],[0,0,0]],                   // Z
  [[6,0,0],[6,6,6],[0,0,0]],                   // J
  [[0,0,7],[7,7,7],[0,0,0]],                   // L
];

const SCORE_TABLE = [0, 100, 300, 500, 800]; // lines cleared: 0-4
const SPEEDS = [800, 720, 640, 560, 480, 400, 340, 280, 220, 160, 100];

// ── DOM ───────────────────────────────────────────────────────────────────────
const boardCanvas = document.getElementById('board');
const nextCanvas  = document.getElementById('next');
const ctx         = boardCanvas.getContext('2d');
const nctx        = nextCanvas.getContext('2d');

const elScore   = document.getElementById('score');
const elLevel   = document.getElementById('level');
const elLines   = document.getElementById('lines');
const elHiScore = document.getElementById('hi-score');
const overlay   = document.getElementById('overlay');
const overlayTitle = document.getElementById('overlay-title');
const overlayScore = document.getElementById('overlay-score');
const btnStart  = document.getElementById('btn-start');
const btnLeft   = document.getElementById('btn-left');
const btnRight  = document.getElementById('btn-right');
const btnRotate = document.getElementById('btn-rotate');
const btnDown   = document.getElementById('btn-down');
const btnDrop   = document.getElementById('btn-drop');

// ── State ─────────────────────────────────────────────────────────────────────
let board, piece, pieceX, pieceY, nextPiece;
let score, level, lines;
let hiScore = parseInt(localStorage.getItem('tetris_hi') || '0', 10);
let running = false;
let dropTimer = null;
let fastDrop = false;

elHiScore.textContent = hiScore;

// ── Board helpers ─────────────────────────────────────────────────────────────
function makeBoard() {
  return Array.from({ length: ROWS }, () => new Array(COLS).fill(0));
}

function rotate(mat) {
  const n = mat.length;
  const m = mat[0].length;
  const out = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let r = 0; r < n; r++)
    for (let c = 0; c < m; c++)
      out[c][n - 1 - r] = mat[r][c];
  return out;
}

function collides(b, p, px, py) {
  for (let r = 0; r < p.length; r++)
    for (let c = 0; c < p[r].length; c++)
      if (p[r][c]) {
        const nx = px + c, ny = py + r;
        if (nx < 0 || nx >= COLS || ny >= ROWS) return true;
        if (ny >= 0 && b[ny][nx]) return true;
      }
  return false;
}

function lock() {
  for (let r = 0; r < piece.length; r++)
    for (let c = 0; c < piece[r].length; c++)
      if (piece[r][c]) {
        if (pieceY + r < 0) { endGame(); return; }
        board[pieceY + r][pieceX + c] = piece[r][c];
      }
  clearLines();
  spawnPiece();
}

function clearLines() {
  let cleared = 0;
  for (let r = ROWS - 1; r >= 0; ) {
    if (board[r].every(v => v !== 0)) {
      board.splice(r, 1);
      board.unshift(new Array(COLS).fill(0));
      cleared++;
    } else r--;
  }
  if (cleared) {
    haptic(cleared >= 4 ? 'heavy' : 'medium');
    lines += cleared;
    score += SCORE_TABLE[cleared] * level;
    level = Math.floor(lines / 10) + 1;
    updateUI();
    resetTimer();
  }
}

function spawnPiece() {
  piece  = nextPiece;
  nextPiece = randomPiece();
  pieceX = Math.floor(COLS / 2) - Math.floor(piece[0].length / 2);
  pieceY = -1;
  if (collides(board, piece, pieceX, pieceY)) { endGame(); }
  drawNext();
}

function randomPiece() {
  const i = Math.floor(Math.random() * (PIECES.length - 1)) + 1;
  return PIECES[i].map(r => [...r]);
}

// ── Game loop ─────────────────────────────────────────────────────────────────
function drop() {
  if (!running) return;
  if (!collides(board, piece, pieceX, pieceY + 1)) {
    pieceY++;
  } else {
    lock();
  }
  draw();
}

function speed() {
  return fastDrop ? 50 : (SPEEDS[Math.min(level - 1, SPEEDS.length - 1)]);
}

function resetTimer() {
  clearInterval(dropTimer);
  dropTimer = setInterval(drop, speed());
}

function startGame() {
  board      = makeBoard();
  score      = 0;
  level      = 1;
  lines      = 0;
  fastDrop   = false;
  nextPiece  = randomPiece();
  spawnPiece();
  running    = true;
  overlay.classList.add('hidden');
  updateUI();
  resetTimer();
  draw();
}

function endGame() {
  running = false;
  clearInterval(dropTimer);
  haptic('heavy');
  if (score > hiScore) {
    hiScore = score;
    localStorage.setItem('tetris_hi', hiScore);
    elHiScore.textContent = hiScore;
  }
  overlayTitle.textContent = 'GAME OVER';
  overlayScore.textContent = `Счёт: ${score}`;
  btnStart.textContent = 'ЕЩЁ РАЗ';
  overlay.classList.remove('hidden');
}

function updateUI() {
  elScore.textContent = score;
  elLevel.textContent = level;
  elLines.textContent = lines;
}

// ── Drawing ───────────────────────────────────────────────────────────────────
function drawCell(context, x, y, colorIdx, cellSize) {
  const color = COLORS[colorIdx];
  if (!color) return;
  context.fillStyle = color;
  context.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
  // highlight
  context.fillStyle = 'rgba(255,255,255,0.18)';
  context.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, 4);
}

function drawGhost() {
  let gy = pieceY;
  while (!collides(board, piece, pieceX, gy + 1)) gy++;
  if (gy === pieceY) return;
  ctx.save();
  ctx.globalAlpha = 0.22;
  for (let r = 0; r < piece.length; r++)
    for (let c = 0; c < piece[r].length; c++)
      if (piece[r][c])
        drawCell(ctx, pieceX + c, gy + r, piece[r][c], CELL);
  ctx.restore();
}

function draw() {
  // background grid
  ctx.fillStyle = getComputedStyle(document.documentElement)
    .getPropertyValue('--surface').trim() || '#16213e';
  ctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);

  ctx.strokeStyle = 'rgba(255,255,255,0.04)';
  ctx.lineWidth = 1;
  for (let c = 0; c <= COLS; c++) {
    ctx.beginPath();
    ctx.moveTo(c * CELL, 0);
    ctx.lineTo(c * CELL, ROWS * CELL);
    ctx.stroke();
  }
  for (let r = 0; r <= ROWS; r++) {
    ctx.beginPath();
    ctx.moveTo(0, r * CELL);
    ctx.lineTo(COLS * CELL, r * CELL);
    ctx.stroke();
  }

  // board cells
  for (let r = 0; r < ROWS; r++)
    for (let c = 0; c < COLS; c++)
      if (board[r][c]) drawCell(ctx, c, r, board[r][c], CELL);

  // ghost
  if (running) drawGhost();

  // active piece
  if (running)
    for (let r = 0; r < piece.length; r++)
      for (let c = 0; c < piece[r].length; c++)
        if (piece[r][c]) drawCell(ctx, pieceX + c, pieceY + r, piece[r][c], CELL);
}

function drawNext() {
  const bg = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg').trim() || '#1a1a2e';
  nctx.fillStyle = bg;
  nctx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);

  const rows = nextPiece.length, cols = nextPiece[0].length;
  const ox = Math.floor((nextCanvas.width  / NEXT_CELL - cols) / 2);
  const oy = Math.floor((nextCanvas.height / NEXT_CELL - rows) / 2);
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++)
      if (nextPiece[r][c]) drawCell(nctx, ox + c, oy + r, nextPiece[r][c], NEXT_CELL);
}

// ── Input: keyboard ───────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (!running) return;
  switch (e.code) {
    case 'ArrowLeft':  moveLeft();   break;
    case 'ArrowRight': moveRight();  break;
    case 'ArrowUp':    tryRotate();  break;
    case 'ArrowDown':
      fastDrop = true;
      resetTimer();
      break;
    case 'Space':
      e.preventDefault();
      hardDrop();
      break;
  }
});

document.addEventListener('keyup', e => {
  if (e.code === 'ArrowDown') { fastDrop = false; resetTimer(); }
});

// ── Input: buttons ────────────────────────────────────────────────────────────
function moveLeft() {
  if (!running) return;
  if (!collides(board, piece, pieceX - 1, pieceY)) { pieceX--; haptic('light'); draw(); }
}
function moveRight() {
  if (!running) return;
  if (!collides(board, piece, pieceX + 1, pieceY)) { pieceX++; haptic('light'); draw(); }
}
function tryRotate() {
  if (!running) return;
  const rot = rotate(piece);
  // wall-kick attempts
  for (const dx of [0, -1, 1, -2, 2]) {
    if (!collides(board, rot, pieceX + dx, pieceY)) {
      piece = rot; pieceX += dx; haptic('light'); draw(); return;
    }
  }
}
function hardDrop() {
  if (!running) return;
  while (!collides(board, piece, pieceX, pieceY + 1)) pieceY++;
  haptic('medium');
  lock();
  draw();
  resetTimer();
}
function softDrop() {
  fastDrop = true; resetTimer();
}
function softDropEnd() {
  fastDrop = false; resetTimer();
}

btnLeft.addEventListener('pointerdown',  e => { e.preventDefault(); moveLeft(); });
btnRight.addEventListener('pointerdown', e => { e.preventDefault(); moveRight(); });
btnRotate.addEventListener('pointerdown', e => { e.preventDefault(); tryRotate(); });
btnDown.addEventListener('pointerdown',  e => { e.preventDefault(); softDrop(); });
btnDown.addEventListener('pointerup',    e => { e.preventDefault(); softDropEnd(); });
btnDown.addEventListener('pointercancel',e => { softDropEnd(); });
btnDrop.addEventListener('pointerdown',  e => { e.preventDefault(); hardDrop(); });
btnStart.addEventListener('click', startGame);

// ── Touch swipe on canvas ─────────────────────────────────────────────────────
let touchStartX = 0, touchStartY = 0, touchLast = 0;

boardCanvas.addEventListener('touchstart', e => {
  e.preventDefault();
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
  touchLast   = Date.now();
}, { passive: false });

boardCanvas.addEventListener('touchend', e => {
  e.preventDefault();
  if (!running) return;
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  const dt = Date.now() - touchLast;
  const absDx = Math.abs(dx), absDy = Math.abs(dy);

  if (dt < 200 && absDx < 15 && absDy < 15) { tryRotate(); return; }
  if (absDx > absDy && absDx > 20) {
    if (dx > 0) moveRight(); else moveLeft();
  } else if (absDy > absDx && absDy > 20) {
    if (dy > 0) hardDrop();
  }
}, { passive: false });

// ── Resize: scale canvas to fit screen width ──────────────────────────────────
function resize() {
  const maxW = Math.min(window.innerWidth - 32, 300);
  const scale = maxW / 300;
  boardCanvas.style.width  = `${300 * scale}px`;
  boardCanvas.style.height = `${600 * scale}px`;
}
window.addEventListener('resize', resize);
resize();

// ── Show start screen ─────────────────────────────────────────────────────────
overlayTitle.textContent = 'ТЕТРИС';
overlayScore.textContent = '';
btnStart.textContent = 'ИГРАТЬ';
overlay.classList.remove('hidden');
draw();
