// Supabase client & API layer for Alisha app
const SUPABASE_URL = 'https://hwqyzftaevrwxtblszoz.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3cXl6ZnRhZXZyd3h0Ymxzem96Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0ODMwMTcsImV4cCI6MjA4OTA1OTAxN30.9zZgfLRF6LeYinGqfMQyo8NRdwi_fzwyIWk44dOEeMc';
const API_BASE = '/api';

// Supabase REST helper
async function sbFetch(path, options = {}) {
  const url = `${SUPABASE_URL}/rest/v1${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'apikey': SUPABASE_ANON_KEY,
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': options.prefer || 'return=representation',
      ...(options.headers || {})
    }
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Supabase error: ${err}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ─── API calls to our backend ──────────────────────────────────────────────

async function apiPost(path, body) {
  const res = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiGet(path) {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ─── DB OPERATIONS ─────────────────────────────────────────────────────────

const DB = {
  // Fetch existing user by telegram_id (used on first open of a new device)
  async getUserByTgId(telegramId) {
    if (!telegramId) return null;
    try {
      return await apiPost('/users/get_by_tg', { telegram_id: telegramId });
    } catch {
      return null;
    }
  },

  // Get or create user by telegram_id
  async upsertUser(telegramId, username, displayName) {
    try {
      return await apiPost('/users/upsert', { telegram_id: telegramId, username, display_name: displayName });
    } catch {
      return this._localUser(telegramId, displayName);
    }
  },

  // Start a new session
  async startSession(userId) {
    try {
      return await apiPost('/sessions/start', { user_id: userId });
    } catch {
      return { id: 'local_' + Date.now() };
    }
  },

  // Complete session with all answers and scores
  async completeSession(sessionId, answers, scores) {
    try {
      return await apiPost('/sessions/complete', { session_id: sessionId, answers, scores });
    } catch {
      this._saveLocalSession(sessionId, answers, scores);
      return { ok: true };
    }
  },

  // Get user stats (sessions, scores history)
  async getUserStats(userId) {
    try {
      return await apiGet(`/users/${userId}/stats`);
    } catch {
      return this._localStats();
    }
  },

  // Get user achievements
  async getUserAchievements(userId) {
    try {
      return await apiGet(`/users/${userId}/achievements`);
    } catch {
      return this._localAchievements();
    }
  },

  // Check and award new achievements
  async checkAchievements(userId) {
    try {
      return await apiPost('/achievements/check', { user_id: userId });
    } catch {
      return [];
    }
  },

  // ─── LOCAL FALLBACK (when API is unavailable) ──────────────────────────

  _localUser(telegramId, displayName) {
    const key = 'alisha_user';
    let user = JSON.parse(localStorage.getItem(key) || 'null');
    if (!user) {
      user = {
        id: telegramId || 'local_' + Date.now(),
        telegram_id: telegramId,
        display_name: displayName || 'Друг',
        streak_days: 0,
        longest_streak: 0,
        total_sessions: 0,
        created_at: new Date().toISOString()
      };
      localStorage.setItem(key, JSON.stringify(user));
    }
    if (displayName && displayName !== user.display_name) {
      user.display_name = displayName;
      localStorage.setItem(key, JSON.stringify(user));
    }
    return user;
  },

  _saveLocalSession(sessionId, answers, scores) {
    const key = 'alisha_sessions';
    const sessions = JSON.parse(localStorage.getItem(key) || '[]');
    sessions.push({ id: sessionId, answers, scores, completed_at: new Date().toISOString() });
    localStorage.setItem(key, JSON.stringify(sessions.slice(-30)));

    // Update user stats
    const user = JSON.parse(localStorage.getItem('alisha_user') || '{}');
    user.total_sessions = (user.total_sessions || 0) + 1;
    user.last_scores = scores;

    // Streak logic
    const today = new Date().toDateString();
    if (user.last_session_date !== today) {
      const yesterday = new Date(Date.now() - 86400000).toDateString();
      if (user.last_session_date === yesterday) {
        user.streak_days = (user.streak_days || 0) + 1;
      } else {
        user.streak_days = 1;
      }
      user.last_session_date = today;
      user.longest_streak = Math.max(user.longest_streak || 0, user.streak_days);
    }
    localStorage.setItem('alisha_user', JSON.stringify(user));
  },

  _localStats() {
    const sessions = JSON.parse(localStorage.getItem('alisha_sessions') || '[]');
    const user = JSON.parse(localStorage.getItem('alisha_user') || '{}');
    return {
      total_sessions: user.total_sessions || 0,
      streak_days: user.streak_days || 0,
      longest_streak: user.longest_streak || 0,
      sessions: sessions.slice(-10).reverse(),
      last_scores: user.last_scores || null
    };
  },

  _localAchievements() {
    return JSON.parse(localStorage.getItem('alisha_achievements') || '[]');
  },

  saveAchievement(achievement) {
    const list = JSON.parse(localStorage.getItem('alisha_achievements') || '[]');
    if (!list.find(a => a.id === achievement.id)) {
      list.push({ ...achievement, earned_at: new Date().toISOString() });
      localStorage.setItem('alisha_achievements', JSON.stringify(list));
    }
  },

  checkLocalAchievements(user, scores) {
    const unlocked = [];
    const earned = JSON.parse(localStorage.getItem('alisha_achievements') || '[]');
    const earnedIds = new Set(earned.map(a => a.id));

    const ALL = [
      { id: 1, name: 'Первый шаг', icon: '🌱', req: () => (user.total_sessions || 0) >= 1 },
      { id: 2, name: 'Открытая душа', icon: '🌺', req: () => (user.total_sessions || 0) >= 5 },
      { id: 3, name: 'Путь к свету', icon: '✨', req: () => (user.total_sessions || 0) >= 10 },
      { id: 4, name: 'Неделя осознанности', icon: '🧘', req: () => (user.streak_days || 0) >= 7 },
      { id: 5, name: 'Кристальное сердце', icon: '💎', req: () => (user.streak_days || 0) >= 14 },
      { id: 6, name: 'Несломимый дух', icon: '🏆', req: () => (user.streak_days || 0) >= 30 },
      { id: 7, name: 'Мастер сна', icon: '🌙', req: () => scores && (scores.sleep || 0) >= 80 },
      { id: 8, name: 'Эмоц. интеллект', icon: '🧠', req: () => scores && (scores.emotions || 0) >= 80 },
      { id: 9, name: 'Гармония', icon: '☯️', req: () => scores && (scores.wellbeing || 0) >= 75 },
      { id: 10, name: 'Победитель привычек', icon: '🌿', req: () => scores && (scores.habits || 0) >= 80 },
    ];

    ALL.forEach(a => {
      if (!earnedIds.has(a.id) && a.req()) {
        this.saveAchievement(a);
        unlocked.push(a);
      }
    });
    return unlocked;
  }
};

// Telegram WebApp helpers
const TG = {
  get app() { return window.Telegram?.WebApp; },
  get user() { return this.app?.initDataUnsafe?.user || null; },
  get userId() { return this.user?.id || null; },
  get username() { return this.user?.username || null; },
  get firstName() { return this.user?.first_name || null; },

  init() {
    if (this.app) {
      this.app.ready();
      this.app.expand();
      // Apply theme
      document.documentElement.style.setProperty('--tg-bg', this.app.themeParams?.bg_color || '#0f0f1a');
    }
  },

  haptic(type = 'light') {
    this.app?.HapticFeedback?.impactOccurred(type);
  },

  close() {
    this.app?.close();
  }
};
