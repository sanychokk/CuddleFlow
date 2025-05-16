# 🤗 CuddleFlow — Telegram Bot for Care & Support

CuddleFlow is a caring Telegram bot designed for couples.  
It helps girls track their menstrual cycles and reminds their partners when it's time to show support (and bring treats 💖🍫).

---

## 🌟 Features

- 👩 For girls:
  - Set and track menstrual cycle
  - Customize cravings (chocolate, chips, etc.)
  - Generate a personal code to connect with a partner

- 👨 For guys:
  - Connect to a partner using a code
  - Get reminders when support is needed
  - See her cravings and "promise" to buy treats

- 🔁 Notifications:
  - Automatic reminders based on the cycle
  - Custom calendar
  - Sweet messages to brighten the day

---

## 🛠️ Tech Stack

- Python 🐍
- [aiogram](https://docs.aiogram.dev) (Telegram Bot Framework)
- SQLite + aiosqlite (for async DB)
- dotenv (for environment variables)
- matplotlib (to generate calendar graphics)

---

## 🚀 Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/sanychokk/CuddleFlow
cd CuddleFlow
```
2. **Create and fill in .env**
```dotenv
BOT_TOKEN=your_telegram_bot_token_here
```
3. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Run the bot**
```bash
python3 bot.py
```
---

## 🐳 Run with Docker

Make sure you have a `.env` file in the root directory.

### Build the image

```bash
docker build -t CuddleBot .
```

## 📂 Project Structure
```
.
├── bot.py          # Main bot logic
├── db.py           # Database logic (aiosqlite)
├── config.py       # Loads token from .env
├── states.py       # FSM states for inputs
├── .env            # Environment variables (keep secret)
├── requirements.txt# Requirements for bot
└── README.md       # This file
```
## ❤️ Author
Made with love by Alex Pavlova

Inspired by care, communication, and chocolate 🍫
