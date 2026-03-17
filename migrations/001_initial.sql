-- Alisha Psychology Bot Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  display_name TEXT NOT NULL DEFAULT 'Друг',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_session_at TIMESTAMPTZ,
  streak_days INTEGER DEFAULT 0,
  longest_streak INTEGER DEFAULT 0,
  total_sessions INTEGER DEFAULT 0,
  last_session_date DATE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  score_wellbeing FLOAT DEFAULT 0,
  score_sleep FLOAT DEFAULT 0,
  score_emotions FLOAT DEFAULT 0,
  score_stress FLOAT DEFAULT 0,
  score_habits FLOAT DEFAULT 0,
  score_social FLOAT DEFAULT 0,
  score_selfesteem FLOAT DEFAULT 0,
  score_purpose FLOAT DEFAULT 0,
  score_physical FLOAT DEFAULT 0
);

-- Answers table
CREATE TABLE IF NOT EXISTS answers (
  id BIGSERIAL PRIMARY KEY,
  session_id BIGINT REFERENCES sessions(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL,
  value_numeric FLOAT,
  value_text TEXT,
  answered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Achievements table
CREATE TABLE IF NOT EXISTS achievements (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  icon TEXT NOT NULL,
  requirement_type TEXT NOT NULL,
  requirement_value INTEGER NOT NULL,
  reward_text TEXT NOT NULL
);

-- User achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
  achievement_id INTEGER REFERENCES achievements(id),
  earned_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, achievement_id)
);

-- Insert achievements
INSERT INTO achievements (id, name, description, icon, requirement_type, requirement_value, reward_text) VALUES
(1, 'Первый шаг', 'Прошёл первую сессию с Алишей', '🌱', 'sessions_total', 1, 'Ты сделал первый шаг к познанию себя! Это требует смелости.'),
(2, 'Открытая душа', 'Прошёл 5 сессий', '🌺', 'sessions_total', 5, 'Твоя открытость восхищает. Алиша гордится тобой!'),
(3, 'Путь к свету', 'Прошёл 10 сессий', '✨', 'sessions_total', 10, 'Ты на пути к глубокому самопознанию. Продолжай!'),
(4, 'Неделя осознанности', '7 дней подряд', '🧘', 'streak_days', 7, 'Неделя работы над собой! Ты получаешь "Печать осознанности" 🔮'),
(5, 'Кристальное сердце', '14 дней подряд', '💎', 'streak_days', 14, 'Две недели! Твоя внутренняя сила растёт. Ты получаешь "Кристальное сердце" 💎'),
(6, 'Несломимый дух', '30 дней подряд', '🏆', 'streak_days', 30, 'МЕСЯЦ! Это невероятно! Ты получаешь "Корону осознанности" 👑'),
(7, 'Мастер сна', 'Score сна > 80', '🌙', 'score_sleep', 80, 'Твой сон стал лучше! Продолжай соблюдать режим.'),
(8, 'Эмоциональный интеллект', 'Score эмоций > 80', '🧠', 'score_emotions', 80, 'Ты научился понимать свои эмоции. Это бесценный навык!'),
(9, 'Гармония', 'Общий score > 75', '☯️', 'score_wellbeing', 75, 'Ты достиг гармонии в своей жизни. Алиша в восторге!'),
(10, 'Победитель привычек', 'Score привычек > 80', '🌿', 'score_habits', 80, 'Ты работаешь над своими привычками. Это изменит твою жизнь!')
ON CONFLICT (id) DO NOTHING;

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for service role, restrict anon)
CREATE POLICY "Allow all for service" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for service" ON sessions FOR ALL USING (true);
CREATE POLICY "Allow all for service" ON answers FOR ALL USING (true);
CREATE POLICY "Allow all for service" ON user_achievements FOR ALL USING (true);
