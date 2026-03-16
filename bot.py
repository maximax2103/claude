"""
News Bot — периодически получает свежие новости через NewsAPI,
генерирует краткую сводку (3-4 предложения) с помощью Claude
и отправляет уведомление в Telegram.
"""

import asyncio
import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import anthropic
import httpx
import schedule
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
NEWS_CATEGORY = os.getenv("NEWS_CATEGORY", "technology")
NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "ru")
NEWS_COUNTRY = os.getenv("NEWS_COUNTRY", "ru")

NEWS_API_BASE = "https://newsapi.org/v2"

# ── State ─────────────────────────────────────────────────────────────────────
sent_article_hashes: set[str] = set()

# ── Clients ───────────────────────────────────────────────────────────────────
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)


# ── NewsAPI ───────────────────────────────────────────────────────────────────

def _article_hash(article: dict) -> str:
    key = article.get("url") or article.get("title", "")
    return hashlib.sha1(key.encode()).hexdigest()


def fetch_top_headlines(hours_back: int = 24) -> list[dict]:
    """Return top headlines not yet sent to the user."""
    params: dict = {
        "apiKey": NEWS_API_KEY,
        "category": NEWS_CATEGORY,
        "language": NEWS_LANGUAGE,
        "pageSize": 10,
    }
    if NEWS_COUNTRY:
        params["country"] = NEWS_COUNTRY

    try:
        resp = httpx.get(f"{NEWS_API_BASE}/top-headlines", params=params, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.error("NewsAPI request failed: %s", exc)
        return []

    articles = resp.json().get("articles", [])

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    fresh = []
    for art in articles:
        published = art.get("publishedAt", "")
        try:
            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pub_dt = datetime.now(timezone.utc)

        if pub_dt < cutoff:
            continue

        h = _article_hash(art)
        if h not in sent_article_hashes:
            fresh.append(art)

    return fresh


# ── Claude summary ────────────────────────────────────────────────────────────

def build_news_text(article: dict) -> str:
    parts = []
    if article.get("title"):
        parts.append(f"Заголовок: {article['title']}")
    if article.get("description"):
        parts.append(f"Описание: {article['description']}")
    if article.get("content"):
        content = article["content"]
        # NewsAPI truncates content — strip the "[+N chars]" suffix
        if "[+" in content:
            content = content[: content.index("[+")]
        parts.append(f"Текст: {content.strip()}")
    return "\n".join(parts)


def generate_summary(article: dict) -> str:
    news_text = build_news_text(article)

    message = claude_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    "На основе информации о новости ниже напиши краткую новостную сводку "
                    "из 3-4 предложений на русском языке. "
                    "Сводка должна быть информативной, нейтральной и легко читаемой. "
                    "Не добавляй заголовок — только текст сводки.\n\n"
                    f"{news_text}"
                ),
            }
        ],
    )
    return message.content[0].text.strip()


# ── Telegram ──────────────────────────────────────────────────────────────────

def format_telegram_message(article: dict, summary: str) -> str:
    source = article.get("source", {}).get("name", "Неизвестный источник")
    title = article.get("title", "")
    url = article.get("url", "")
    published = article.get("publishedAt", "")

    try:
        pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        time_str = pub_dt.strftime("%d.%m.%Y %H:%M UTC")
    except (ValueError, AttributeError):
        time_str = published

    lines = [
        f"📰 <b>{title}</b>",
        "",
        summary,
        "",
        f"🕐 {time_str}",
        f"📡 {source}",
    ]
    if url:
        lines.append(f'🔗 <a href="{url}">Читать полностью</a>')

    return "\n".join(lines)


async def send_notification(article: dict, summary: str) -> None:
    text = format_telegram_message(article, summary)
    await telegram_bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=False,
    )


# ── Main loop ─────────────────────────────────────────────────────────────────

async def process_news() -> None:
    log.info("Fetching headlines (category=%s, lang=%s, country=%s)…",
             NEWS_CATEGORY, NEWS_LANGUAGE, NEWS_COUNTRY or "any")
    articles = fetch_top_headlines()

    if not articles:
        log.info("No new articles found.")
        return

    log.info("Found %d new article(s).", len(articles))

    for article in articles:
        title = article.get("title", "—")
        log.info("Processing: %s", title)

        try:
            summary = generate_summary(article)
        except anthropic.APIError as exc:
            log.error("Claude API error: %s", exc)
            continue

        try:
            await send_notification(article, summary)
            sent_article_hashes.add(_article_hash(article))
            log.info("Notification sent.")
        except TelegramError as exc:
            log.error("Telegram error: %s", exc)

        # Avoid hitting rate limits
        await asyncio.sleep(1)


def job() -> None:
    asyncio.run(process_news())


async def main() -> None:
    log.info("News bot started. Poll interval: %d min.", POLL_INTERVAL)

    # Run immediately on startup
    await process_news()

    schedule.every(POLL_INTERVAL).minutes.do(job)

    while True:
        schedule.run_pending()
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
