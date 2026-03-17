// Dashboard charts and analytics using Chart.js

const DIMENSION_LABELS = {
  sleep:      'Сон',
  emotions:   'Эмоции',
  stress:     'Спокойствие',
  habits:     'Привычки',
  social:     'Общение',
  selfesteem: 'Самооценка',
  purpose:    'Смысл',
  physical:   'Здоровье'
};

const DIMENSION_COLORS = {
  sleep:      '#A78BFA',
  emotions:   '#F472B6',
  stress:     '#60A5FA',
  habits:     '#34D399',
  social:     '#FBBF24',
  selfesteem: '#F87171',
  purpose:    '#818CF8',
  physical:   '#2DD4BF'
};

const DIMENSION_ICONS = {
  sleep:      '🌙',
  emotions:   '💙',
  stress:     '🌊',
  habits:     '🌿',
  social:     '🤝',
  selfesteem: '💫',
  purpose:    '🔥',
  physical:   '⚡'
};

function getScoreLabel(score) {
  if (score >= 85) return { text: 'Отлично', color: '#34D399' };
  if (score >= 70) return { text: 'Хорошо', color: '#60A5FA' };
  if (score >= 55) return { text: 'Средне', color: '#FBBF24' };
  if (score >= 40) return { text: 'Требует внимания', color: '#F87171' };
  return { text: 'Нужна забота', color: '#EF4444' };
}

function getWellbeingEmoji(score) {
  if (score >= 85) return '🌟';
  if (score >= 70) return '😊';
  if (score >= 55) return '🙂';
  if (score >= 40) return '😐';
  return '💙';
}

// Radar chart
function renderRadarChart(canvasId, scores) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const dims = Object.keys(DIMENSION_LABELS);
  const data = dims.map(d => scores[d] || 0);
  const labels = dims.map(d => DIMENSION_LABELS[d]);

  // Destroy existing
  if (canvas._chart) canvas._chart.destroy();

  canvas._chart = new Chart(canvas, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Твоё состояние',
        data,
        backgroundColor: 'rgba(167, 139, 250, 0.18)',
        borderColor: '#A78BFA',
        borderWidth: 2.5,
        pointBackgroundColor: dims.map(d => DIMENSION_COLORS[d]),
        pointBorderColor: '#fff',
        pointBorderWidth: 1.5,
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 25,
            color: 'rgba(255,255,255,0.3)',
            font: { size: 9 },
            backdropColor: 'transparent'
          },
          grid: { color: 'rgba(255,255,255,0.1)' },
          angleLines: { color: 'rgba(255,255,255,0.1)' },
          pointLabels: {
            color: 'rgba(255,255,255,0.85)',
            font: { size: 11, weight: '500' }
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.raw}/100`
          }
        }
      }
    }
  });
}

// Trend line chart (last 7 sessions)
function renderTrendChart(canvasId, sessions) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (canvas._chart) canvas._chart.destroy();

  const labels = sessions.map((s, i) => {
    if (s.completed_at) {
      const d = new Date(s.completed_at);
      return `${d.getDate()}.${d.getMonth() + 1}`;
    }
    return `#${i + 1}`;
  });

  const wellbeing = sessions.map(s => s.scores?.wellbeing || s.score_wellbeing || 0);

  canvas._chart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Общее состояние',
        data: wellbeing,
        borderColor: '#A78BFA',
        backgroundColor: 'rgba(167,139,250,0.15)',
        fill: true,
        tension: 0.45,
        pointBackgroundColor: '#A78BFA',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${Math.round(ctx.raw)}/100`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: 'rgba(255,255,255,0.55)', font: { size: 11 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: 'rgba(255,255,255,0.55)', font: { size: 11 }, stepSize: 25 }
        }
      }
    }
  });
}

// Render score cards in a container
function renderScoreCards(containerId, scores) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';
  const dims = Object.keys(DIMENSION_LABELS);

  dims.forEach(dim => {
    const val = scores[dim] || 0;
    const { text, color } = getScoreLabel(val);
    const icon = DIMENSION_ICONS[dim];
    const label = DIMENSION_LABELS[dim];
    const clr = DIMENSION_COLORS[dim];

    const card = document.createElement('div');
    card.className = 'score-card';
    card.innerHTML = `
      <div class="score-card-header">
        <span class="score-icon">${icon}</span>
        <span class="score-label">${label}</span>
        <span class="score-value" style="color:${clr}">${val}</span>
      </div>
      <div class="score-bar-bg">
        <div class="score-bar-fill" style="width:${val}%;background:${clr}"></div>
      </div>
      <div class="score-status" style="color:${color}">${text}</div>
    `;
    container.appendChild(card);
  });
}

// Render achievement badges
function renderAchievements(containerId, earned, all) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '';
  const earnedIds = new Set((earned || []).map(a => a.achievement_id || a.id));

  const ALL_ACHIEVEMENTS = [
    { id: 1, name: 'Первый шаг', icon: '🌱', description: 'Прошёл первую сессию' },
    { id: 2, name: 'Открытая душа', icon: '🌺', description: '5 сессий пройдено' },
    { id: 3, name: 'Путь к свету', icon: '✨', description: '10 сессий пройдено' },
    { id: 4, name: 'Неделя осознанности', icon: '🧘', description: '7 дней подряд' },
    { id: 5, name: 'Кристальное сердце', icon: '💎', description: '14 дней подряд' },
    { id: 6, name: 'Несломимый дух', icon: '🏆', description: '30 дней подряд' },
    { id: 7, name: 'Мастер сна', icon: '🌙', description: 'Сон > 80 баллов' },
    { id: 8, name: 'Эмоц. интеллект', icon: '🧠', description: 'Эмоции > 80 баллов' },
    { id: 9, name: 'Гармония', icon: '☯️', description: 'Общий > 75 баллов' },
    { id: 10, name: 'Здоровые привычки', icon: '🌿', description: 'Привычки > 80 баллов' },
  ];

  ALL_ACHIEVEMENTS.forEach(a => {
    const isEarned = earnedIds.has(a.id);
    const badge = document.createElement('div');
    badge.className = `achievement-badge ${isEarned ? 'earned' : 'locked'}`;
    badge.innerHTML = `
      <div class="badge-icon">${isEarned ? a.icon : '🔒'}</div>
      <div class="badge-name">${a.name}</div>
      <div class="badge-desc">${a.description}</div>
      ${isEarned ? '<div class="badge-earned">Получено ✓</div>' : ''}
    `;
    container.appendChild(badge);
  });
}

// Wellbeing index ring (SVG)
function renderWellbeingRing(containerId, score) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const r = 52;
  const circumference = 2 * Math.PI * r;
  const filled = (score / 100) * circumference;
  const { text, color } = getScoreLabel(score);
  const emoji = getWellbeingEmoji(score);

  container.innerHTML = `
    <svg width="130" height="130" viewBox="0 0 130 130">
      <circle cx="65" cy="65" r="${r}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10"/>
      <circle cx="65" cy="65" r="${r}" fill="none" stroke="${color}" stroke-width="10"
        stroke-dasharray="${filled} ${circumference}"
        stroke-dashoffset="${circumference / 4}"
        stroke-linecap="round"
        style="transition: stroke-dasharray 1.2s ease"/>
      <text x="65" y="58" text-anchor="middle" font-size="26" fill="white">${emoji}</text>
      <text x="65" y="78" text-anchor="middle" font-size="20" font-weight="bold" fill="white">${score}</text>
      <text x="65" y="93" text-anchor="middle" font-size="10" fill="rgba(255,255,255,0.6)">${text}</text>
    </svg>
  `;
}
