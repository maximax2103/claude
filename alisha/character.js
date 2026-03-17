// Alisha Spirit — CSS/DOM animated character (replaces Three.js)
// A glowing ethereal orb with an expressive face and aura

class AlinaCharacter {
  constructor(container) {
    this.container = container;
    this.state = 'idle';
    this._build();
    this._startIdleLoop();
  }

  _build() {
    this.container.innerHTML = `
      <div class="alisha-spirit" id="alisha-spirit">
        <div class="spirit-aura a1"></div>
        <div class="spirit-aura a2"></div>
        <div class="spirit-aura a3"></div>
        <div class="spirit-orb">
          <div class="spirit-glow"></div>
          <div class="spirit-face">
            <div class="spirit-eyes">
              <div class="spirit-eye eye-l">
                <div class="eye-pupil"></div>
                <div class="eye-shine"></div>
              </div>
              <div class="spirit-eye eye-r">
                <div class="eye-pupil"></div>
                <div class="eye-shine"></div>
              </div>
            </div>
            <div class="spirit-mouth"></div>
          </div>
          <div class="spirit-blush blush-l"></div>
          <div class="spirit-blush blush-r"></div>
        </div>
        <div class="spirit-particles">
          <span class="p1">✦</span>
          <span class="p2">✦</span>
          <span class="p3">✧</span>
          <span class="p4">✦</span>
          <span class="p5">✧</span>
        </div>
      </div>
    `;

    this.el     = this.container.querySelector('#alisha-spirit');
    this.eyeL   = this.container.querySelector('.eye-l');
    this.eyeR   = this.container.querySelector('.eye-r');
    this.mouth  = this.container.querySelector('.spirit-mouth');
    this.blushL = this.container.querySelector('.blush-l');
    this.blushR = this.container.querySelector('.blush-r');
  }

  setState(state) {
    if (this.state === state) return;
    this.state = state;
    const s = this.el;
    s.className = 'alisha-spirit state-' + state;
  }

  startSpeaking() { this.setState('speaking'); }
  stopSpeaking()  { this.setState('idle'); }

  showHappy() {
    this.setState('happy');
    setTimeout(() => this.setState('idle'), 2500);
  }

  showExcited() {
    this.setState('excited');
    setTimeout(() => this.setState('idle'), 3000);
  }

  showThinking() { this.setState('thinking'); }

  showWaving() {
    this.setState('waving');
    setTimeout(() => this.setState('idle'), 3000);
  }

  _startIdleLoop() {
    // periodic blink
    const blink = () => {
      if (this.state === 'idle' || this.state === 'speaking' || this.state === 'waving') {
        this.eyeL.classList.add('blink');
        this.eyeR.classList.add('blink');
        setTimeout(() => {
          this.eyeL.classList.remove('blink');
          this.eyeR.classList.remove('blink');
        }, 160);
      }
      setTimeout(blink, 2500 + Math.random() * 3000);
    };
    setTimeout(blink, 2000 + Math.random() * 2000);
  }

  destroy() {
    this.container.innerHTML = '';
  }
}
