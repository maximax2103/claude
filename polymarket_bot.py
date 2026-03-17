"""
Polymarket Price Alert Bot
Отслеживает резкое изменение цен на рынках с объёмом > $50k.
Уведомляет в Telegram если цена изменилась > 10% за 10 минут.
"""

import asyncio
import json
import logging
import re
import os
import time
from collections import defaultdict, deque
from datetime import datetime

import httpx
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Настройки ────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "482744886")

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"

MIN_VOLUME = 200_000       # минимальный объём рынка в $
PRICE_CHANGE_PCT = 10.0    # порог изменения цены в %
WINDOW_MINUTES = 10        # окно наблюдения в минутах
POLL_INTERVAL = 60         # интервал опроса в секундах
MARKETS_LIMIT = 100        # сколько топ-рынков загружать за раз

# Разрешённые категории (теги рынков на Polymarket)
ALLOWED_TAGS = {
    "politics", "sports", "crypto", "iran", "geopolitics", "tech", "weather",
}

# Рынки которые слишком часто триггерят алерты — блокируем на сессию
noisy_markets: dict[str, int] = {}  # market_id -> кол-во алертов
NOISY_THRESHOLD = 5  # больше N алертов = шумный рынок

# ── Хранилище истории цен ─────────────────────────────────────────────────────
# price_history[token_id] = deque of (timestamp, price)
price_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=WINDOW_MINUTES + 2))

# Чтобы не спамить одно и то же уведомление
last_alert: dict[str, float] = {}
ALERT_COOLDOWN = 600  # 10 минут между повторными алертами для одного токена


async def fetch_active_markets(client: httpx.AsyncClient) -> list[dict]:
    """Получить активные рынки с объёмом > MIN_VOLUME."""
    markets = []
    offset = 0

    while True:
        try:
            r = await client.get(
                f"{GAMMA_API}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "order": "volume24hr",
                    "ascending": "false",
                    "limit": MARKETS_LIMIT,
                    "offset": offset,
                },
                timeout=15,
            )
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            log.error("Ошибка загрузки рынков: %s", e)
            break

        if not batch:
            break

        if offset == 0 and batch:
            log.info("Пример рынка (ключи): %s", list(batch[0].keys()))
            log.info("tokens=%s clobTokenIds=%s", batch[0].get("tokens"), batch[0].get("clobTokenIds"))

        for m in batch:
            try:
                vol = float(m.get("volume", 0) or 0)
            except (TypeError, ValueError):
                vol = 0

            if vol < MIN_VOLUME:
                return markets

            # Фильтр по категориям через теги
            tags_raw = m.get("tags") or []
            if isinstance(tags_raw, str):
                try:
                    tags_raw = json.loads(tags_raw)
                except Exception:
                    tags_raw = []
            market_tags = {
                (t.get("slug") or t.get("label") or "").lower()
                for t in tags_raw
                if isinstance(t, dict)
            }
            if not market_tags.intersection(ALLOWED_TAGS):
                continue

            markets.append(m)

        if len(batch) < MARKETS_LIMIT:
            break

        offset += MARKETS_LIMIT

    log.info("Загружено рынков с объёмом > $%.0f: %d", MIN_VOLUME, len(markets))
    return markets


async def fetch_mid_price(client: httpx.AsyncClient, token_id: str) -> float | None:
    """Получить mid-price токена через CLOB API."""
    try:
        r = await client.get(
            f"{CLOB_API}/midpoint",
            params={"token_id": token_id},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        mid = data.get("mid")
        if mid is not None:
            return float(mid)
    except Exception as e:
        log.debug("Ошибка получения цены для %s: %s", token_id, e)
    return None


def check_price_spike(token_id: str, current_price: float) -> float | None:
    """
    Проверяет, изменилась ли цена более чем на PRICE_CHANGE_PCT%
    за последние WINDOW_MINUTES минут.
    Возвращает процент изменения (+ или -) или None если порог не достигнут.
    """
    history = price_history[token_id]
    now = time.time()
    window_start = now - WINDOW_MINUTES * 60

    # Найти самую раннюю цену строго в пределах окна (не старше WINDOW_MINUTES минут)
    baseline_price = None
    baseline_ts = None
    for ts, price in history:
        if ts >= window_start:
            baseline_price = price
            baseline_ts = ts
            break

    # Если нет данных в окне или baseline слишком старый — не считаем
    if baseline_price is None or baseline_price == 0:
        return None
    if now - baseline_ts > WINDOW_MINUTES * 60:
        return None

    change_pct = (current_price - baseline_price) / baseline_price * 100

    if abs(change_pct) >= PRICE_CHANGE_PCT:
        return change_pct

    return None


def format_alert(market: dict, token: dict, change_pct: float, current_price: float) -> str:
    """Форматировать сообщение об алерте."""
    direction = "📈" if change_pct > 0 else "📉"
    outcome = token.get("outcome", "?")
    question = market.get("question", "Неизвестный рынок")
    volume = float(market.get("volume", 0) or 0)
    slug = market.get("slug") or market.get("id", "")
    slug_clean = re.sub(r'-\d+$', '', slug)
    url = f"https://polymarket.com/event/{slug_clean}"

    sign = "+" if change_pct > 0 else ""

    return (
        f"{direction} <b>Резкое изменение цены на Polymarket</b>\n\n"
        f"<b>{question}</b>\n"
        f"Исход: <b>{outcome}</b>\n\n"
        f"Цена сейчас: <b>{current_price:.1%}</b>\n"
        f"Изменение за 10 мин: <b>{sign}{change_pct:.1f}%</b>\n"
        f"Объём: <b>${volume:,.0f}</b>\n\n"
        f"🔗 <a href=\"{url}\">Открыть рынок</a>"
    )


async def monitor_loop(bot: Bot):
    """Основной цикл мониторинга."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                markets = await fetch_active_markets(client)

                # Собираем все токены для мониторинга
                token_to_market: dict[str, dict] = {}
                token_to_info: dict[str, dict] = {}

                for market in markets:
                    # Gamma API возвращает токены как JSON-строку в clobTokenIds
                    clob_ids_raw = market.get("clobTokenIds")
                    if clob_ids_raw:
                        try:
                            clob_ids = json.loads(clob_ids_raw) if isinstance(clob_ids_raw, str) else clob_ids_raw
                        except Exception:
                            clob_ids = []
                        outcomes_raw = market.get("outcomes")
                        try:
                            outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else (outcomes_raw or [])
                        except Exception:
                            outcomes = []
                        for idx, token_id in enumerate(clob_ids):
                            outcome = outcomes[idx] if idx < len(outcomes) else str(idx)
                            token_to_market[token_id] = market
                            token_to_info[token_id] = {"token_id": token_id, "outcome": outcome}
                    else:
                        # Fallback: старый формат с полем tokens
                        tokens = market.get("tokens") or []
                        for token in tokens:
                            token_id = token.get("token_id")
                            if token_id:
                                token_to_market[token_id] = market
                                token_to_info[token_id] = token

                log.info("Проверяем цены для %d токенов...", len(token_to_market))

                # Запрашиваем цены параллельно (батчами по 20)
                token_ids = list(token_to_market.keys())
                batch_size = 20

                for i in range(0, len(token_ids), batch_size):
                    batch = token_ids[i : i + batch_size]
                    prices = await asyncio.gather(
                        *[fetch_mid_price(client, tid) for tid in batch]
                    )

                    now = time.time()
                    for token_id, price in zip(batch, prices):
                        if price is None:
                            continue

                        # Записываем в историю
                        price_history[token_id].append((now, price))

                        # Проверяем спайк
                        change_pct = check_price_spike(token_id, price)
                        if change_pct is None:
                            continue

                        # Проверяем cooldown
                        last = last_alert.get(token_id, 0)
                        if now - last < ALERT_COOLDOWN:
                            continue

                        last_alert[token_id] = now
                        market = token_to_market[token_id]
                        market_id = market.get("id", "")

                        # Пропускаем шумные рынки
                        noisy_markets[market_id] = noisy_markets.get(market_id, 0) + 1
                        if noisy_markets[market_id] > NOISY_THRESHOLD:
                            log.info("Шумный рынок пропущен: %s (%d алертов)", market.get("question", "?")[:50], noisy_markets[market_id])
                            continue

                        token_info = token_to_info[token_id]
                        text = format_alert(market, token_info, change_pct, price)

                        log.info(
                            "АЛЕРТ: %s | %s | %.1f%%",
                            market.get("question", "?")[:60],
                            token_info.get("outcome", "?"),
                            change_pct,
                        )

                        try:
                            await bot.send_message(
                                chat_id=TELEGRAM_CHAT_ID,
                                text=text,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True,
                            )
                        except Exception as e:
                            log.error("Ошибка отправки Telegram: %s", e)

                    # Небольшая пауза между батчами чтобы не перегружать API
                    await asyncio.sleep(0.5)

            except Exception as e:
                log.exception("Ошибка в основном цикле: %s", e)

            log.info("Следующий опрос через %d сек.", POLL_INTERVAL)
            await asyncio.sleep(POLL_INTERVAL)


async def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в .env")

    bot = Bot(token=TELEGRAM_TOKEN)

    me = await bot.get_me()
    log.info("Бот запущен: @%s", me.username)

    # Стартовое сообщение
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=(
            "🚀 <b>Polymarket Price Alert Bot запущен</b>\n\n"
            f"Отслеживаю рынки с объёмом > <b>${MIN_VOLUME:,}</b>\n"
            f"Порог срабатывания: изменение > <b>{PRICE_CHANGE_PCT}%</b> за <b>{WINDOW_MINUTES} мин</b>\n"
            f"Интервал опроса: <b>{POLL_INTERVAL} сек</b>"
        ),
        parse_mode=ParseMode.HTML,
    )

    await monitor_loop(bot)


if __name__ == "__main__":
    asyncio.run(main())
