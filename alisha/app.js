// Alisha — Personal Psychology Bot
// Main application controller

const App = {
  // State
  screen: null,
  user: null,
  character: null,
  session: null,
  sessionAnswers: [],
  sessionQuestions: [],
  currentQIndex: 0,
  previousQuestionIds: [],
  scores: null,
  stats: null,
  newAchievements: [],

  // ─── INIT ──────────────────────────────────────────────────────────────────
  async init() {
    TG.init();

    // Load previous question IDs
    this.previousQuestionIds = JSON.parse(localStorage.getItem('alisha_prev_qids') || '[]');

    // Init 3D character
    const charContainer = document.getElementById('char-canvas');
    if (charContainer && window.THREE) {
      this.character = new AlinaCharacter(charContainer);
    }

    // Determine starting screen
    const savedUser = JSON.parse(localStorage.getItem('alisha_user') || 'null');
    if (savedUser && savedUser.display_name && savedUser.display_name !== 'Друг') {
      this.user = savedUser;
      // Try to sync with backend
      try {
        this.user = await DB.upsertUser(TG.userId, TG.username, savedUser.display_name);
        localStorage.setItem('alisha_user', JSON.stringify(this.user));
      } catch {}
      await this.showHome();
    } else {
      await this.showWelcome();
    }
  },

  // ─── SCREEN MANAGEMENT ────────────────────────────────────────────────────
  showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(id);
    if (screen) {
      screen.classList.add('active');
      this.screen = id;
    }
  },

  // ─── WELCOME ──────────────────────────────────────────────────────────────
  async showWelcome() {
    this.showScreen('screen-welcome');
    this._speak('Привет! Я Алиша 👋\nТвой личный психолог и друг.\n\nКак мне тебя называть?', 3000);
    setTimeout(() => {
      this.showScreen('screen-name');
      if (this.character) this.character.setState('idle');
    }, 3500);
  },

  // ─── NAME INPUT ───────────────────────────────────────────────────────────
  async submitName() {
    const input = document.getElementById('name-input');
    const name = (input?.value || '').trim();
    if (!name || name.length < 2) {
      this._shake(input);
      return;
    }

    TG.haptic('medium');

    try {
      this.user = await DB.upsertUser(TG.userId || ('local_' + Date.now()), TG.username, name);
      localStorage.setItem('alisha_user', JSON.stringify(this.user));
    } catch {
      this.user = DB._localUser(TG.userId, name);
    }

    this.showScreen('screen-intro');
    this._speak(`Приятно познакомиться, ${name}! 💙\n\nЯ задам тебе несколько вопросов, чтобы лучше понять тебя и помочь найти твои точки роста.\n\nГотов?`, 0);
    if (this.character) this.character.showHappy();
  },

  // ─── SESSION INTRO ────────────────────────────────────────────────────────
  async startSession() {
    TG.haptic('medium');
    // Select 30 questions
    this.sessionQuestions = selectSessionQuestions(30, this.previousQuestionIds);
    this.sessionAnswers = [];
    this.currentQIndex = 0;

    // Start session in DB
    try {
      this.session = await DB.startSession(this.user?.id);
    } catch {
      this.session = { id: 'local_' + Date.now() };
    }

    this._showQuestion();
  },

  // ─── QUESTION FLOW ────────────────────────────────────────────────────────
  _showQuestion() {
    const q = this.sessionQuestions[this.currentQIndex];
    if (!q) {
      this._finishSession();
      return;
    }

    const total = this.sessionQuestions.length;
    const progress = ((this.currentQIndex) / total) * 100;

    document.getElementById('q-progress-fill').style.width = progress + '%';
    document.getElementById('q-counter').textContent = `${this.currentQIndex + 1} / ${total}`;

    // Show question in panel text element
    const qTextEl = document.getElementById('q-text');
    if (qTextEl) qTextEl.textContent = q.text;

    // Also speak it via speech bubble (shorter version)
    const shortText = q.text.length > 90 ? q.text.substring(0, 90) + '...' : q.text;
    this._speak(shortText, 0);
    if (this.character) this.character.startSpeaking();

    // Render answer UI
    const ansContainer = document.getElementById('answer-container');
    ansContainer.innerHTML = '';
    ansContainer.className = 'answer-container';

    if (q.type === 'scale') {
      this._renderScale(ansContainer, q);
    } else if (q.type === 'yesno') {
      this._renderYesNo(ansContainer, q);
    } else if (q.type === 'choice') {
      this._renderChoice(ansContainer, q);
    }

    this.showScreen('screen-question');
  },

  _renderScale(container, q) {
    container.classList.add('scale-mode');
    let value = 5;

    container.innerHTML = `
      <div class="scale-value-display">
        <span id="scale-val">${value}</span>
        <span class="scale-max">/10</span>
      </div>
      <div class="scale-track">
        <input type="range" id="scale-input" min="1" max="10" value="${value}" step="1" class="scale-slider">
        <div class="scale-labels">
          <span>${q.low_label || '1'}</span>
          <span>${q.high_label || '10'}</span>
        </div>
      </div>
      <div class="scale-emojis">
        <span>😔</span><span>😐</span><span>😊</span><span>😄</span><span>🌟</span>
      </div>
      <button class="btn-answer" onclick="App._answerScale()">Далее →</button>
    `;

    const slider = container.querySelector('#scale-input');
    const display = container.querySelector('#scale-val');
    slider.addEventListener('input', () => {
      value = parseInt(slider.value);
      display.textContent = value;
      display.style.color = value <= 3 ? '#F87171' : value <= 6 ? '#FBBF24' : '#34D399';
      TG.haptic('light');
    });
  },

  _answerScale() {
    const slider = document.getElementById('scale-input');
    const val = parseInt(slider?.value || 5);
    this._recordAnswer(val);
  },

  _renderYesNo(container, q) {
    container.classList.add('yesno-mode');
    container.innerHTML = `
      <div class="yesno-buttons">
        <button class="btn-yesno btn-yes" onclick="App._answerYesNo(true)">
          <span class="yesno-icon">✓</span>
          <span>Да</span>
        </button>
        <button class="btn-yesno btn-no" onclick="App._answerYesNo(false)">
          <span class="yesno-icon">✗</span>
          <span>Нет</span>
        </button>
      </div>
    `;
  },

  _answerYesNo(yes) {
    const q = this.sessionQuestions[this.currentQIndex];
    // For bad habits (pos=false): yes=0, no=10; for good: yes=10, no=0
    let val;
    if (q.pos === false) {
      val = yes ? 2 : 10;
    } else {
      val = yes ? 10 : 2;
    }
    this._recordAnswer(val, yes ? 'yes' : 'no');
  },

  _renderChoice(container, q) {
    container.classList.add('choice-mode');
    const btns = (q.options || []).map((opt, i) => `
      <button class="btn-choice" onclick="App._answerChoice(${i})">
        <span class="choice-num">${i + 1}</span>
        <span class="choice-text">${opt}</span>
      </button>
    `).join('');
    container.innerHTML = `<div class="choice-list">${btns}</div>`;
  },

  _answerChoice(idx) {
    const q = this.sessionQuestions[this.currentQIndex];
    const score = (q.scores || [])[idx] ?? 5;
    const text = (q.options || [])[idx] || '';
    this._recordAnswer(score, text);
  },

  _recordAnswer(numericVal, textVal = null) {
    TG.haptic('light');
    const q = this.sessionQuestions[this.currentQIndex];

    this.sessionAnswers.push({
      question_id: q.id,
      value_numeric: numericVal,
      value_text: textVal
    });

    this.previousQuestionIds.push(q.id);
    if (this.character) this.character.stopSpeaking();

    this.currentQIndex++;

    // Short delay for UX
    setTimeout(() => this._showQuestion(), 280);
  },

  // ─── SESSION COMPLETE ─────────────────────────────────────────────────────
  async _finishSession() {
    // Save used question IDs
    localStorage.setItem('alisha_prev_qids', JSON.stringify(this.previousQuestionIds.slice(-90)));

    // Calculate scores
    this.scores = calculateScores(this.sessionAnswers);

    // Show processing screen
    this.showScreen('screen-processing');
    if (this.character) this.character.showThinking();
    this._speak('Даю тебе обратную связь...\nАнализирую твои ответы 🔍', 0);

    // Save to DB
    try {
      await DB.completeSession(this.session.id, this.sessionAnswers, this.scores);
    } catch {
      DB._saveLocalSession(this.session.id, this.sessionAnswers, this.scores);
    }

    // Check achievements
    const updatedUser = JSON.parse(localStorage.getItem('alisha_user') || '{}');
    this.newAchievements = DB.checkLocalAchievements(updatedUser, this.scores);

    await new Promise(r => setTimeout(r, 1800));

    this._showResults();
  },

  _showResults() {
    const s = this.scores;
    const name = this.user?.display_name || 'Друг';

    // Wellbeing ring
    renderWellbeingRing('result-ring', s.wellbeing);

    // Score cards
    renderScoreCards('result-cards', s);

    // Advice
    const advice = getAliashaAdvice(s);
    const adviceEl = document.getElementById('result-advice');
    if (adviceEl) {
      adviceEl.innerHTML = advice.map(a => `<div class="advice-item">💙 ${a}</div>`).join('');
    }

    // Alisha message
    const emoji = getWellbeingEmoji(s.wellbeing);
    this._speak(`${name}, вот твой результат ${emoji}\n\nИндекс благополучия: ${s.wellbeing}/100\n\n${advice[0] || ''}`, 0);
    if (this.character) this.character.showHappy();

    // New achievements popup
    if (this.newAchievements.length > 0) {
      setTimeout(() => this._showAchievementPopup(this.newAchievements[0]), 2000);
    }

    this.showScreen('screen-results');
  },

  _showAchievementPopup(achievement) {
    const popup = document.getElementById('achievement-popup');
    if (!popup) return;
    document.getElementById('popup-icon').textContent = achievement.icon;
    document.getElementById('popup-name').textContent = achievement.name;
    popup.classList.add('visible');
    TG.haptic('heavy');
    setTimeout(() => popup.classList.remove('visible'), 4000);
  },

  // ─── HOME / DASHBOARD ─────────────────────────────────────────────────────
  async showHome() {
    this.showScreen('screen-loading');

    try {
      this.stats = await DB.getUserStats(this.user?.id);
    } catch {
      this.stats = DB._localStats();
    }

    const name = this.user?.display_name || 'Друг';
    document.getElementById('home-name').textContent = name;
    document.getElementById('home-streak').textContent = this.stats.streak_days || 0;
    document.getElementById('home-sessions').textContent = this.stats.total_sessions || 0;

    const lastScores = this.stats.last_scores || (this.stats.sessions?.[0]?.scores);
    if (lastScores) {
      renderWellbeingRing('home-ring', lastScores.wellbeing || 0);
    } else {
      renderWellbeingRing('home-ring', 0);
    }

    const hasHistory = (this.stats.sessions?.length || 0) > 1;
    if (hasHistory && lastScores) {
      renderRadarChart('home-radar', lastScores);
    }

    // Greeting based on time
    const h = new Date().getHours();
    let greeting = h < 12 ? 'Доброе утро' : h < 18 ? 'Добрый день' : 'Добрый вечер';
    this._speak(`${greeting}, ${name}! 💙\n\nЯ рядом. Готова к новой сессии?`, 0);

    this.showScreen('screen-home');
  },

  async showDashboard() {
    this.showScreen('screen-loading');

    try {
      this.stats = await DB.getUserStats(this.user?.id);
    } catch {
      this.stats = DB._localStats();
    }

    const lastScores = this.stats.last_scores || this.stats.sessions?.[0]?.scores;

    if (lastScores) {
      renderRadarChart('dash-radar', lastScores);
      renderScoreCards('dash-cards', lastScores);
      renderWellbeingRing('dash-ring', lastScores.wellbeing || 0);
    } else {
      document.getElementById('dash-empty')?.classList.remove('hidden');
    }

    // Trend chart
    const sessions = (this.stats.sessions || []).slice(0, 7).reverse();
    if (sessions.length > 1) {
      renderTrendChart('dash-trend', sessions);
    }

    this.showScreen('screen-dashboard');
  },

  async showAchievements() {
    const earned = DB._localAchievements();
    renderAchievements('achievements-list', earned, []);

    const count = earned.length;
    document.getElementById('ach-count').textContent = `${count} / 10`;

    this.showScreen('screen-achievements');
  },

  // ─── HELPERS ──────────────────────────────────────────────────────────────
  _speak(text, clearAfter = 0) {
    const bubble = document.getElementById('speech-bubble');
    const bubbleText = document.getElementById('bubble-text');
    if (!bubble || !bubbleText) return;

    bubbleText.innerHTML = text.replace(/\n/g, '<br>');
    bubble.classList.add('visible');

    if (this.character) this.character.startSpeaking();

    if (clearAfter > 0) {
      clearTimeout(this._speakTimer);
      this._speakTimer = setTimeout(() => {
        bubble.classList.remove('visible');
        if (this.character) this.character.stopSpeaking();
      }, clearAfter);
    } else {
      if (this.character) setTimeout(() => this.character.stopSpeaking(), 2500);
    }
  },

  _shake(el) {
    if (!el) return;
    el.classList.add('shake');
    setTimeout(() => el.classList.remove('shake'), 500);
    TG.haptic('heavy');
  },

  goToHome() { this.showHome(); },
  goToDashboard() { this.showDashboard(); },
  goToAchievements() { this.showAchievements(); },
};

// Boot
document.addEventListener('DOMContentLoaded', () => {
  // Check Three.js loaded
  if (!window.THREE) {
    console.warn('Three.js not loaded');
  }
  App.init();
});
