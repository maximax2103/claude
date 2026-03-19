"""
MrBeast Polymarket Monitor Bot
================================
Мониторит просмотры MrBeast и сигнализирует держать ли ставку NO на 116B
Установка:
    pip install python-telegram-bot[job-queue] requests schedule
Запуск:
    python mrbeast_bot.py
Переменные которые нужно заполнить:
    TELEGRAM_TOKEN  — токен от @BotFather
    YOUTUBE_API_KEY — ключ от Google Cloud (YouTube Data API v3)
    CHAT_ID         — твой Telegram chat_id (получишь при первом /start)
"""
import requests
import schedule
import time
import json
import math
import os
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ══════════════════════════════════════════
#  КОНФИГ — заполни свои данные
# ══════════════════════════════════════════
TELEGRAM_TOKEN  = "8567336295:AAELXPVdObDO7Xqcj7nygUW-rYpTOl5zUGM"
YOUTUBE_API_KEY = "AIzaSyCGxnvQDEhznYV7SqQJYm0-tJjASd1AHx4"  # ← пересоздай этот ключ!
CHAT_ID         = 482744886

# Параметры рынка
TARGET_VIEWS      = 116_000_000_000   # 116B — цель рынка
DEADLINE          = datetime(2026, 3, 31, 23, 59, 0, tzinfo=timezone.utc)
MRBEAST_CHANNEL   = "UCX6OQ3DkcsbYNE6H8uQQuVA"

# Параметры стратегии
WEEKDAY_AVG       = 80_000_000    # 80M в будни
WEEKEND_AVG       = 130_000_000   # 130M в выходные
SIGMA_DAILY       = 24_500_000    # стандартное отклонение
MARKET_NO_PRICE   = 0.48          # текущая цена NO на рынке (обнови вручную)

# Файл для хранения вчерашних просмотров
STATE_FILE = "views_state.json"

# ══════════════════════════════════════════
#  YOUTUBE API
# ══════════════════════════════════════════
def get_current_views() -> int:
    """Получает текущее количество просмотров канала MrBeast"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics",
        "id": MRBEAST_CHANNEL,
        "key": YOUTUBE_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        views = int(data["items"][0]["statistics"]["viewCount"])
        return views
    except Exception as e:
        print(f"[YouTube API Error] {e}")
        return None

# ══════════════════════════════════════════
#  STATE — сохранение предыдущих просмотров
# ══════════════════════════════════════════
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_views": None, "last_date": None, "history": []}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ══════════════════════════════════════════
#  МАТЕМАТИКА
# ══════════════════════════════════════════
def days_until_deadline() -> int:
    now = datetime.now(timezone.utc)
    delta = DEADLINE - now
    return max(0, delta.days + (1 if delta.seconds > 0 else 0))

def count_weekdays_weekends(days: int) -> tuple:
    """Считает будни и выходные в оставшихся днях"""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    weekdays = 0
    weekends = 0
    for i in range(days):
        day = (now + timedelta(days=i)).weekday()
        if day >= 5:  # суббота=5, воскресенье=6
            weekends += 1
        else:
            weekdays += 1
    return weekdays, weekends

def calculate_probability(current_views: int, daily_delta: int = None) -> dict:
    """
    Считает вероятность достижения 116B к дедлайну.
    Возвращает полный анализ.
    """
    days_left = days_until_deadline()
    views_needed = TARGET_VIEWS - current_views

    if views_needed <= 0:
        return {
            "probability": 1.0,
            "views_needed": 0,
            "views_needed_b": 0,
            "days_left": days_left,
            "signal": "RESOLVED_YES",
            "verdict": "🎯 Цель уже достигнута!"
        }

    if days_left == 0:
        return {
            "probability": 0.0,
            "views_needed": views_needed,
            "views_needed_b": views_needed / 1e9,
            "days_left": 0,
            "signal": "RESOLVED_NO",
            "verdict": "⏰ Время вышло"
        }

    # Взвешенное среднее буд/вых
    weekdays, weekends = count_weekdays_weekends(days_left)
    expected_total = weekdays * WEEKDAY_AVG + weekends * WEEKEND_AVG
    expected_daily_avg = expected_total / days_left

    # Если есть свежие данные — обновляем байесовски
    if daily_delta and daily_delta > 0:
        # Байесовское обновление: взвешиваем 70% структурный прогноз + 30% последний день
        bayesian_daily = 0.7 * expected_daily_avg + 0.3 * daily_delta
        note = f"байес с последним днём {daily_delta/1e6:.1f}M"
    else:
        bayesian_daily = expected_daily_avg
        note = "структурный прогноз буд/вых"

    expected_total_bayesian = bayesian_daily * days_left

    # Нормальное распределение для суммы за N дней
    sigma_total = SIGMA_DAILY * math.sqrt(days_left)

    # Z-score
    z = (views_needed - expected_total_bayesian) / sigma_total

    # P(Z >= z) через complementary error function
    from math import erfc, sqrt
    prob = erfc(z / sqrt(2)) / 2
    prob = max(0.001, min(0.999, prob))

    # EV расчёт
    ev_no = (1 - prob) * (1 - MARKET_NO_PRICE) - prob * MARKET_NO_PRICE

    # Сигнал
    if prob < 0.05:
        signal = "HOLD_NO"
        verdict = "🔴 ДЕРЖАТЬ NO — вероятность очень низкая"
    elif prob < 0.15:
        signal = "HOLD_NO_WEAK"
        verdict = "🟡 ДЕРЖАТЬ NO — слабый шанс для YES"
    elif prob < 0.30:
        signal = "CAUTION"
        verdict = "⚠️ ОСТОРОЖНО — пересмотри позицию"
    elif prob < 0.50:
        signal = "CONSIDER_EXIT"
        verdict = "🟠 РАССМОТРИ ВЫХОД из NO"
    else:
        signal = "EXIT_NO"
        verdict = "🟢 ВЫЙТИ из NO — вероятность высокая"

    return {
        "probability": round(prob, 4),
        "views_needed": views_needed,
        "views_needed_b": views_needed / 1e9,
        "days_left": days_left,
        "weekdays": weekdays,
        "weekends": weekends,
        "expected_daily": bayesian_daily,
        "expected_total": expected_total_bayesian,
        "sigma_total": sigma_total,
        "z_score": round(z, 2),
        "ev_no": round(ev_no, 4),
        "signal": signal,
        "verdict": verdict,
        "note": note
    }

# ══════════════════════════════════════════
#  ФОРМАТИРОВАНИЕ СООБЩЕНИЯ
# ══════════════════════════════════════════
def format_report(current_views: int, daily_delta: int, calc: dict) -> str:
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    views_b = current_views / 1e9
    needed_b = calc["views_needed_b"]

    ev_sign = "+" if calc["ev_no"] >= 0 else ""
    ev_color = "🟢" if calc["ev_no"] > 0.1 else "🟡" if calc["ev_no"] > 0 else "🔴"

    delta_str = f"+{daily_delta/1e6:.1f}M" if daily_delta else "н/д"

    lines = [
        f"📊 *MrBeast 116B Monitor*",
        f"🕐 {now_str}",
        f"",
        f"👁 Просмотры сейчас: *{views_b:.3f}B*",
        f"📈 Прирост за сутки: *{delta_str}*",
        f"🎯 До цели 116B: *{needed_b:.3f}B*",
        f"⏳ Дней осталось: *{calc['days_left']}* ({calc['weekdays']} буд / {calc['weekends']} вых)",
        f"",
        f"━━━━━━━━━━━━━━━",
        f"🧮 *Расчёт*",
        f"Ожид. прирост/день: {calc['expected_daily']/1e6:.1f}M ({calc['note']})",
        f"Ожид. итого: {calc['expected_total']/1e6:.0f}M",
        f"Z-score: {calc['z_score']}",
        f"",
        f"📉 *P(YES)* = *{calc['probability']*100:.1f}%*",
        f"📉 *P(NO)*  = *{(1-calc['probability'])*100:.1f}%*",
        f"",
        f"💰 *EV на Buy NO @ {MARKET_NO_PRICE*100:.0f}¢*",
        f"{ev_color} EV = *{ev_sign}{calc['ev_no']:.3f}* на каждый $1",
        f"",
        f"━━━━━━━━━━━━━━━",
        f"🚦 *{calc['verdict']}*",
    ]

    # Доп. рекомендация
    if calc["signal"] in ("HOLD_NO", "HOLD_NO_WEAK"):
        lines.append(f"")
        lines.append(f"💡 Ставка математически оправдана. Держи.")
    elif calc["signal"] == "CAUTION":
        lines.append(f"")
        lines.append(f"💡 Следи за дневным приростом. Если >100M — пересмотри.")
    elif calc["signal"] in ("CONSIDER_EXIT", "EXIT_NO"):
        lines.append(f"")
        lines.append(f"💡 Вероятность выросла. Рассмотри фиксацию прибыли.")

    return "\n".join(lines)

# ══════════════════════════════════════════
#  TELEGRAM КОМАНДЫ
# ══════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id

    # Сохраняем chat_id
    state = load_state()
    state["chat_id"] = CHAT_ID
    save_state(state)

    await update.message.reply_text(
        f"👋 Бот запущен!\n"
        f"Chat ID: `{CHAT_ID}`\n\n"
        f"Команды:\n"
        f"/status — текущий анализ\n"
        f"/price 48 — обновить цену NO (в центах)\n"
        f"/help — справка\n\n"
        f"Авторепорт приходит каждый день в 09:00",
        parse_mode="Markdown"
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Получаю данные...")

    current_views = get_current_views()
    if not current_views:
        await update.message.reply_text("❌ Ошибка YouTube API. Проверь ключ.")
        return

    state = load_state()
    last_views = state.get("last_views")
    daily_delta = (current_views - last_views) if last_views else None

    calc = calculate_probability(current_views, daily_delta)
    msg = format_report(current_views, daily_delta, calc)

    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MARKET_NO_PRICE
    try:
        new_price = float(context.args[0]) / 100
        MARKET_NO_PRICE = new_price
        await update.message.reply_text(f"✅ Цена NO обновлена: {new_price*100:.0f}¢")
    except:
        await update.message.reply_text("Использование: /price 48")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Как работает бот:*\n\n"
        "1. Каждые сутки в 09:00 пишет авторепорт\n"
        "2. Считает P(YES) через нормальное распределение\n"
        "3. Учитывает буд/вых (80M vs 130M)\n"
        "4. Байесовски обновляет прогноз по последнему дню\n"
        "5. Считает EV на позицию NO\n\n"
        "*Сигналы:*\n"
        "🔴 ДЕРЖАТЬ NO — P(YES) < 5%\n"
        "🟡 ДЕРЖАТЬ NO — P(YES) 5-15%\n"
        "⚠️ ОСТОРОЖНО — P(YES) 15-30%\n"
        "🟠 РАССМОТРИ ВЫХОД — P(YES) 30-50%\n"
        "🟢 ВЫЙТИ из NO — P(YES) > 50%\n\n"
        "*Команды:*\n"
        "/status — мгновенный анализ\n"
        "/price 48 — обновить цену NO\n",
        parse_mode="Markdown"
    )

# ══════════════════════════════════════════
#  ЕЖЕДНЕВНЫЙ АВТОРЕПОРТ
# ══════════════════════════════════════════
async def daily_report(app):
    """Отправляет ежедневный отчёт"""
    state = load_state()
    chat_id = state.get("chat_id") or CHAT_ID

    if not chat_id:
        print("[Bot] chat_id не задан — сначала отправь /start боту")
        return

    current_views = get_current_views()
    if not current_views:
        await app.bot.send_message(chat_id=chat_id, text="❌ Ошибка YouTube API при авторепорте")
        return

    last_views = state.get("last_views")
    daily_delta = (current_views - last_views) if last_views else None

    # Обновляем state
    state["last_views"] = current_views
    state["last_date"] = datetime.now().isoformat()
    if daily_delta:
        history = state.get("history", [])
        history.append({"date": state["last_date"], "delta": daily_delta})
        state["history"] = history[-30:]  # храним последние 30 дней
    save_state(state)

    calc = calculate_probability(current_views, daily_delta)
    msg = format_report(current_views, daily_delta, calc)

    await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
    print(f"[Bot] Авторепорт отправлен: {datetime.now()}")

# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════
def main():
    print("🤖 MrBeast Monitor Bot запускается...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("help", cmd_help))

    # Ежедневный репорт в 09:00 через job queue
    app.job_queue.run_daily(
        lambda ctx: app.create_task(daily_report(app)),
        time=datetime.strptime("09:00", "%H:%M").time()
    )

    print("✅ Бот запущен. Жди /start в Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()
