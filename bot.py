"""
Alisha Psychology Bot — Telegram Bot
Opens the Web App via inline keyboard button.
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "друг"

    keyboard = [[
        InlineKeyboardButton(
            "💙 Открыть Алишу",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "Я *Алиша* — твой личный психолог.\n\n"
        "Я помогу тебе:\n"
        "• 💬 Понять своё внутреннее состояние\n"
        "• 📊 Отслеживать прогресс в динамике\n"
        "• 🌱 Работать над своими слабыми местами\n"
        "• 🏆 Получать награды за работу над собой\n\n"
        "Нажми кнопку ниже, чтобы начать 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "💙 Открыть Алишу",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤗 *Алиша — Личный психолог*\n\n"
        "Команды:\n"
        "/start — Начать\n"
        "/help — Помощь\n"
        "/alisha — Открыть приложение\n\n"
        "Приложение поможет тебе лучше понять себя через регулярные сессии вопросов "
        "о твоём самочувствии, привычках, эмоциях и целях.",
        parse_mode="Markdown",
        reply_markup=markup
    )


async def alisha_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "💙 Открыть Алишу",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Алиша ждёт тебя 💙\nНажми кнопку, чтобы начать сессию:",
        reply_markup=markup
    )


async def web_app_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from the Web App."""
    data = update.effective_message.web_app_data.data
    logger.info(f"WebApp data received: {data}")
    try:
        import json
        parsed = json.loads(data)
        action = parsed.get("action")
        if action == "session_complete":
            score = parsed.get("wellbeing_score", 0)
            name = parsed.get("user_name", "Друг")
            await update.message.reply_text(
                f"✅ {name}, сессия завершена!\n"
                f"🌟 Индекс благополучия: *{score}/100*\n\n"
                f"Продолжай работать над собой — это требует смелости 💙",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error parsing WebApp data: {e}")


async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton(
            "💙 Открыть Алишу",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Хочешь поговорить с Алишей? Нажми кнопку 💙",
        reply_markup=markup
    )


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in .env!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_cmd))
    app.add_handler(CommandHandler("alisha", alisha_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    logger.info("Alisha Bot started! 💙")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
