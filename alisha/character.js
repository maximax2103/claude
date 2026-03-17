// Alisha — Anime character (CSS/SVG, no Three.js required)

class AlinaCharacter {
  constructor(container) {
    this.container = container;
    this.state = 'idle';
    this._speaking = false;
    this._blinkTimer = null;
    this._idleTimer = null;
    this._mouthTimer = null;
    this._build();
    this._startIdleLoop();
  }

  _build() {
    this.container.innerHTML = `
<div class="alisha-anime" id="alisha-anime">
  <svg class="alisha-svg" viewBox="0 0 200 230" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="ag-skin" cx="42%" cy="28%" r="65%">
        <stop offset="0%"   stop-color="#FFEDE2"/>
        <stop offset="70%"  stop-color="#F5C9A8"/>
        <stop offset="100%" stop-color="#E8B08A"/>
      </radialGradient>
      <radialGradient id="ag-eye-l" cx="38%" cy="32%" r="56%">
        <stop offset="0%"   stop-color="#FFE840"/>
        <stop offset="42%"  stop-color="#F0A000"/>
        <stop offset="100%" stop-color="#8A5E00"/>
      </radialGradient>
      <radialGradient id="ag-eye-r" cx="38%" cy="32%" r="56%">
        <stop offset="0%"   stop-color="#FFE840"/>
        <stop offset="42%"  stop-color="#F0A000"/>
        <stop offset="100%" stop-color="#8A5E00"/>
      </radialGradient>
      <radialGradient id="ag-hair" cx="50%" cy="18%" r="80%">
        <stop offset="0%"   stop-color="#E03030"/>
        <stop offset="55%"  stop-color="#BE1E22"/>
        <stop offset="100%" stop-color="#8A1014"/>
      </radialGradient>
    </defs>

    <!-- ── HAIR BACK ── -->
    <path d="M 28 128 Q 24 60 100 36 Q 176 60 172 128 Q 164 198 152 230 L 48 230 Q 36 198 28 128 Z"
          fill="#B01C20"/>
    <!-- side strands -->
    <path d="M 30 118 Q 13 155 17 196 Q 21 218 32 230"
          stroke="#C42028" stroke-width="13" fill="none" stroke-linecap="round"/>
    <path d="M 170 118 Q 187 155 183 196 Q 179 218 168 230"
          stroke="#C42028" stroke-width="13" fill="none" stroke-linecap="round"/>

    <!-- ── NECK + CLOTHES ── -->
    <rect x="85" y="186" width="30" height="36" rx="8" fill="url(#ag-skin)"/>
    <path d="M 8 230 Q 36 206 85 196 L 85 230 Z"  fill="#18182A"/>
    <path d="M 192 230 Q 164 206 115 196 L 115 230 Z" fill="#18182A"/>
    <rect x="72" y="213" width="56" height="17" fill="#EBEBEB" rx="4"/>
    <!-- collar line -->
    <path d="M 85 196 Q 100 210 115 196" stroke="#D0D0D0" stroke-width="1.5" fill="none"/>

    <!-- ── FACE ── -->
    <ellipse cx="100" cy="128" rx="68" ry="72" fill="url(#ag-skin)"/>
    <!-- subtle chin shadow -->
    <ellipse cx="100" cy="190" rx="44" ry="20" fill="rgba(190,120,80,0.09)"/>

    <!-- ── HAIR FRONT / BANGS ── -->
    <path d="M 32 106
             Q 34 58 100 38
             Q 166 58 168 106
             Q 155 76 141 89
             Q 129 61 117 77
             Q 109 50 100 62
             Q 91 50 83 77
             Q 71 61 59 89
             Q 45 76 32 106 Z"
          fill="url(#ag-hair)"/>
    <!-- center bang depth -->
    <path d="M 83 77 Q 81 98 80 113 Q 88 86 100 92 Q 112 86 120 113 Q 119 98 117 77 Q 110 58 100 64 Q 90 58 83 77 Z"
          fill="#9E1820" opacity="0.75"/>
    <!-- left bang shadow -->
    <path d="M 32 106 Q 44 116 48 133 Q 52 107 64 97 Q 46 99 32 106 Z" fill="#921416"/>
    <!-- right bang shadow -->
    <path d="M 168 106 Q 156 116 152 133 Q 148 107 136 97 Q 154 99 168 106 Z" fill="#921416"/>
    <!-- hair highlight gloss -->
    <path d="M 72 46 Q 67 65 72 84" stroke="rgba(255,185,165,0.48)" stroke-width="3.5" fill="none" stroke-linecap="round"/>
    <path d="M 91 40 Q 88 59 91 78" stroke="rgba(255,170,150,0.32)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M 110 40 Q 113 59 110 78" stroke="rgba(255,165,145,0.22)" stroke-width="2" fill="none" stroke-linecap="round"/>

    <!-- ── EYEBROWS ── -->
    <path id="ebrow-l" d="M 60 102 Q 74 95 88 98" stroke="#761010" stroke-width="3" fill="none" stroke-linecap="round"/>
    <path id="ebrow-r" d="M 112 98 Q 126 95 140 102" stroke="#761010" stroke-width="3" fill="none" stroke-linecap="round"/>

    <!-- ── EYE SOCKETS shadow ── -->
    <ellipse cx="72"  cy="122" rx="20" ry="18" fill="rgba(180,110,80,0.1)"/>
    <ellipse cx="128" cy="122" rx="20" ry="18" fill="rgba(180,110,80,0.1)"/>

    <!-- ── EYE WHITES ── -->
    <ellipse class="eye-w-l" cx="72"  cy="120" rx="18" ry="16" fill="white"/>
    <ellipse class="eye-w-r" cx="128" cy="120" rx="18" ry="16" fill="white"/>
    <!-- top-lid shadow on white -->
    <ellipse cx="72"  cy="112" rx="18" ry="9" fill="rgba(200,150,130,0.13)"/>
    <ellipse cx="128" cy="112" rx="18" ry="9" fill="rgba(200,150,130,0.13)"/>

    <!-- ── IRIS ── -->
    <ellipse cx="72"  cy="121" rx="12" ry="13" fill="url(#ag-eye-l)"/>
    <ellipse cx="128" cy="121" rx="12" ry="13" fill="url(#ag-eye-r)"/>

    <!-- ── PUPILS ── -->
    <ellipse id="p-l" cx="72"  cy="122" rx="5.5" ry="7" fill="#160600"/>
    <ellipse id="p-r" cx="128" cy="122" rx="5.5" ry="7" fill="#160600"/>

    <!-- ── SHINE ── -->
    <ellipse cx="77"  cy="114" rx="4"   ry="3.5" fill="rgba(255,255,255,0.95)"/>
    <ellipse cx="133" cy="114" rx="4"   ry="3.5" fill="rgba(255,255,255,0.95)"/>
    <ellipse cx="67"  cy="126" rx="1.8" ry="1.8" fill="rgba(255,255,255,0.58)"/>
    <ellipse cx="123" cy="126" rx="1.8" ry="1.8" fill="rgba(255,255,255,0.58)"/>

    <!-- ── TOP EYELID LINE ── -->
    <path d="M 54 111 Q 67 103 91 109" stroke="#160606" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M 109 109 Q 133 103 146 111" stroke="#160606" stroke-width="2.5" fill="none" stroke-linecap="round"/>

    <!-- ── EYELASHES LEFT ── -->
    <line x1="55"  y1="111" x2="51"  y2="105" stroke="#160606" stroke-width="2"   stroke-linecap="round"/>
    <line x1="62"  y1="105" x2="59"  y2="99"  stroke="#160606" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="72"  y1="103" x2="71"  y2="97"  stroke="#160606" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="90"  y1="109" x2="93"  y2="103" stroke="#160606" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="83"  y1="105" x2="86"  y2="99"  stroke="#160606" stroke-width="1.5" stroke-linecap="round"/>

    <!-- ── EYELASHES RIGHT ── -->
    <line x1="145" y1="111" x2="149" y2="105" stroke="#160606" stroke-width="2"   stroke-linecap="round"/>
    <line x1="138" y1="105" x2="141" y2="99"  stroke="#160606" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="128" y1="103" x2="129" y2="97"  stroke="#160606" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="110" y1="109" x2="107" y2="103" stroke="#160606" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="117" y1="105" x2="114" y2="99"  stroke="#160606" stroke-width="1.5" stroke-linecap="round"/>

    <!-- ── BOTTOM LASH LINE ── -->
    <path d="M 55  131 Q 72  135 90  131" stroke="#BF9080" stroke-width="0.9" fill="none" stroke-linecap="round"/>
    <path d="M 110 131 Q 128 135 145 131" stroke="#BF9080" stroke-width="0.9" fill="none" stroke-linecap="round"/>

    <!-- ── NOSE ── -->
    <path d="M 97 153 Q 100 158 103 153" stroke="#D4A090" stroke-width="1.8" fill="none" stroke-linecap="round"/>

    <!-- ── MOUTH (closed smile) ── -->
    <path id="mouth-c" d="M 88 168 Q 100 177 112 168"
          stroke="#C07070" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <!-- MOUTH open (speaking) -->
    <path id="mouth-o" d="M 88 168 Q 94 180 100 182 Q 106 180 112 168"
          stroke="#B05858" stroke-width="2" fill="#DFA0A0" stroke-linecap="round" opacity="0"/>

    <!-- ── BLUSH ── -->
    <ellipse class="blush-l" cx="56"  cy="143" rx="14" ry="7" fill="rgba(255,128,128,0.28)"/>
    <ellipse class="blush-r" cx="144" cy="143" rx="14" ry="7" fill="rgba(255,128,128,0.28)"/>
  </svg>
  <div id="alisha-sparkles" class="anime-sparkles"></div>
</div>`;

    this.el       = this.container.querySelector('#alisha-anime');
    this.mouthC   = this.container.querySelector('#mouth-c');
    this.mouthO   = this.container.querySelector('#mouth-o');
    this.blushL   = this.container.querySelector('.blush-l');
    this.blushR   = this.container.querySelector('.blush-r');
    this.ebrowL   = this.container.querySelector('#ebrow-l');
    this.ebrowR   = this.container.querySelector('#ebrow-r');
    this.pupilL   = this.container.querySelector('#p-l');
    this.pupilR   = this.container.querySelector('#p-r');
    this.eyeWL    = this.container.querySelector('.eye-w-l');
    this.eyeWR    = this.container.querySelector('.eye-w-r');
  }

  // ─── IDLE LOOP ────────────────────────────────────────────────────────────
  _startIdleLoop() {
    this.setState('idle');
    const scheduleBlink = () => {
      this._blinkTimer = setTimeout(() => { this._blink(); scheduleBlink(); },
        2400 + Math.random() * 3200);
    };
    scheduleBlink();

    const scheduleGlance = () => {
      this._idleTimer = setTimeout(() => {
        if (this.state === 'idle') this._glance();
        scheduleGlance();
      }, 4500 + Math.random() * 7000);
    };
    scheduleGlance();
  }

  _blink() {
    if (!this.eyeWL || !this.eyeWR) return;
    // squish eyes vertically
    [this.eyeWL, this.eyeWR].forEach(e => e.setAttribute('ry', '2'));
    setTimeout(() => {
      [this.eyeWL, this.eyeWR].forEach(e => e.setAttribute('ry', '16'));
    }, 110);
  }

  _glance() {
    if (!this.pupilL || !this.pupilR) return;
    const d = Math.random() > 0.5 ? 3 : -3;
    this.pupilL.setAttribute('cx', 72  + d);
    this.pupilR.setAttribute('cx', 128 + d);
    setTimeout(() => {
      this.pupilL.setAttribute('cx', 72);
      this.pupilR.setAttribute('cx', 128);
    }, 1100);
  }

  // ─── STATE HELPERS ────────────────────────────────────────────────────────
  setState(state) {
    if (!this.el) return;
    this.state = state;
    this.el.className = `alisha-anime state-${state}`;
  }

  showWaving() {
    this.setState('waving');
    this._setBlush('rgba(255,110,110,0.55)');
    setTimeout(() => { this._setBlush('rgba(255,128,128,0.28)'); this.setState('idle'); }, 3000);
  }

  showHappy() {
    this.setState('happy');
    this._setBlush('rgba(255,100,110,0.6)');
    if (this.mouthC) this.mouthC.setAttribute('d', 'M 86 166 Q 100 179 114 166');
    this._spawnSparkles();
    setTimeout(() => {
      this._setBlush('rgba(255,128,128,0.28)');
      if (this.mouthC) this.mouthC.setAttribute('d', 'M 88 168 Q 100 177 112 168');
      this.setState('idle');
    }, 3600);
  }

  showThinking() {
    this.setState('thinking');
    if (this.ebrowL) this.ebrowL.setAttribute('d', 'M 60 98 Q 74 91 88 95');
    setTimeout(() => {
      if (this.ebrowL) this.ebrowL.setAttribute('d', 'M 60 102 Q 74 95 88 98');
    }, 4500);
  }

  startSpeaking() {
    this.setState('speaking');
    this._speaking = true;
    this._animateMouth();
  }

  stopSpeaking() {
    this._speaking = false;
    clearTimeout(this._mouthTimer);
    if (this.mouthO) this.mouthO.setAttribute('opacity', '0');
    if (this.mouthC) this.mouthC.setAttribute('opacity', '1');
    if (this.state === 'speaking') this.setState('idle');
  }

  // ─── INTERNAL ─────────────────────────────────────────────────────────────
  _animateMouth() {
    if (!this._speaking) return;
    const open = this.mouthO?.getAttribute('opacity') !== '1';
    this.mouthO?.setAttribute('opacity', open ? '1' : '0');
    this.mouthC?.setAttribute('opacity', open ? '0' : '1');
    this._mouthTimer = setTimeout(() => this._animateMouth(), 150 + Math.random() * 130);
  }

  _setBlush(color) {
    this.blushL?.setAttribute('fill', color);
    this.blushR?.setAttribute('fill', color);
  }

  _spawnSparkles() {
    const box = this.container.querySelector('#alisha-sparkles');
    if (!box) return;
    ['✦','✧','✨','💫','⭐'].forEach((sym, i) => {
      setTimeout(() => {
        const s = document.createElement('span');
        s.className = 'sparkle-item';
        s.textContent = sym;
        s.style.left = (18 + Math.random() * 64) + '%';
        s.style.top  = (8  + Math.random() * 55) + '%';
        box.appendChild(s);
        setTimeout(() => s.remove(), 1100);
      }, i * 140);
    });
  }
}
