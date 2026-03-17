# Alisha — Setup Guide

## 1. Supabase Migration
Go to your Supabase project → SQL Editor → paste and run `migrations/001_initial.sql`

## 2. Configure environment
```
cp .env.example .env
# Fill in: BOT_TOKEN, WEBAPP_URL, SUPABASE_SERVICE_KEY (optional)
```

## 3. Install dependencies
```
pip install -r requirements.txt
```

## 4. Run server
```
python server.py
```
Serves the Web App at `http://localhost:8000` and API at `/api/*`

## 5. Run bot (separate terminal)
```
python bot.py
```

## 6. Expose publicly
Use ngrok or deploy to Railway/Render:
```
ngrok http 8000
# Set WEBAPP_URL=https://xxx.ngrok.io in .env, restart bot
```
