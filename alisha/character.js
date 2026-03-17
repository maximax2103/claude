// Alisha — Image-based character with CSS animations

class AlinaCharacter {
  constructor(container) {
    this.container = container;
    this.state = 'idle';
    this._speaking = false;
    this._blinkTimer = null;
    this._mouthTimer = null;
    this._build();
    this._startIdleLoop();
  }

  _build() {
    this.container.innerHTML = `
<div class="alisha-wrap" id="alisha-wrap">
  <!-- Glow behind character -->
  <div class="alisha-glow" id="alisha-glow"></div>

  <!-- Character portrait -->
  <div class="alisha-portrait" id="alisha-portrait">
    <img
      src="assets/alisha.png"
      class="alisha-img"
      id="alisha-img"
      alt="Алиша"
      draggable="false"
      onerror="this.style.display='none'; document.getElementById('alisha-fallback').style.display='flex'"
    />
    <!-- Fallback if image not loaded -->
    <div class="alisha-fallback" id="alisha-fallback" style="display:none">
      <div class="alisha-fallback-inner">
        <div class="fb-hair"></div>
        <div class="fb-face">
          <div class="fb-eyes">
            <div class="fb-eye"><div class="fb-iris"></div></div>
            <div class="fb-eye"><div class="fb-iris"></div></div>
          </div>
          <div class="fb-mouth" id="fb-mouth"></div>
        </div>
      </div>
    </div>

    <!-- Speaking mouth overlay (only used in speaking state) -->
    <div class="alisha-mouth-overlay" id="alisha-mouth-ov"></div>
  </div>

  <!-- Sparkle container -->
  <div class="alisha-sparkles" id="alisha-sparkles"></div>
</div>`;

    this.el       = this.container.querySelector('#alisha-wrap');
    this.portrait = this.container.querySelector('#alisha-portrait');
    this.glow     = this.container.querySelector('#alisha-glow');
    this.img      = this.container.querySelector('#alisha-img');
  }

  // ─── IDLE ─────────────────────────────────────────────────────────────────
  _startIdleLoop() {
    this.setState('idle');
    const schedBlink = () => {
      this._blinkTimer = setTimeout(() => {
        this._doBlink(); schedBlink();
      }, 2600 + Math.random() * 3400);
    };
    schedBlink();
  }

  _doBlink() {
    if (!this.portrait) return;
    this.portrait.classList.add('blinking');
    setTimeout(() => this.portrait.classList.remove('blinking'), 140);
  }

  // ─── STATES ───────────────────────────────────────────────────────────────
  setState(state) {
    if (!this.el) return;
    this.state = state;
    this.el.className = `alisha-wrap state-${state}`;
  }

  showWaving() {
    this.setState('waving');
    this._pulseGlow('rgba(220,80,80,0.6)');
    setTimeout(() => { this._resetGlow(); this.setState('idle'); }, 3000);
  }

  showHappy() {
    this.setState('happy');
    this._pulseGlow('rgba(255,140,60,0.65)');
    this._spawnSparkles();
    setTimeout(() => { this._resetGlow(); this.setState('idle'); }, 3800);
  }

  showThinking() {
    this.setState('thinking');
    this._pulseGlow('rgba(100,120,255,0.4)');
    setTimeout(() => { this._resetGlow(); if (this.state === 'thinking') this.setState('idle'); }, 5000);
  }

  startSpeaking() {
    this.setState('speaking');
    this._speaking = true;
    this._pulseGlow('rgba(180,50,50,0.45)');
    this._animateMouth();
  }

  stopSpeaking() {
    this._speaking = false;
    clearTimeout(this._mouthTimer);
    if (this.state === 'speaking') { this._resetGlow(); this.setState('idle'); }
  }

  // ─── INTERNAL ─────────────────────────────────────────────────────────────
  _animateMouth() {
    if (!this._speaking) return;
    if (this.portrait) this.portrait.classList.toggle('mouth-open');
    this._mouthTimer = setTimeout(() => this._animateMouth(), 155 + Math.random() * 120);
  }

  _pulseGlow(color) {
    if (this.glow) this.glow.style.background =
      `radial-gradient(ellipse at 50% 60%, ${color} 0%, transparent 65%)`;
  }

  _resetGlow() {
    if (this.glow) this.glow.style.background = '';
  }

  _spawnSparkles() {
    const box = this.container.querySelector('#alisha-sparkles');
    if (!box) return;
    ['✦','✧','✨','💫','⭐'].forEach((s, i) => {
      setTimeout(() => {
        const el = document.createElement('span');
        el.className = 'sparkle-item';
        el.textContent = s;
        el.style.left = (15 + Math.random() * 70) + '%';
        el.style.top  = (10 + Math.random() * 60) + '%';
        box.appendChild(el);
        setTimeout(() => el.remove(), 1100);
      }, i * 130);
    });
  }
}
