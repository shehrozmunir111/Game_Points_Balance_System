# Game Points & Balance System — Telegram Bot

A production ready Telegram bot system for tracking player points with a FastAPI backend, PostgreSQL database, and full Docker deployment.

## Architecture

```
┌──────────────┐     HTTP/JSON      ┌──────────────┐     SQL/asyncpg     ┌──────────────┐
│  Telegram Bot │ ◄───────────────► │ FastAPI API   │ ◄───────────────► │  PostgreSQL  │
│  (aiogram)    │                   │ (Uvicorn)     │                   │              │
└──────────────┘                   └──────────────┘                   └──────────────┘
```

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN from @BotFather
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

The system will:
- Start PostgreSQL
- Run Alembic migrations automatically
- Start the FastAPI backend on port 8000
- Start the Telegram bot

## Bot Commands

### Player Commands
| Command | Description |
|---------|-------------|
| `/start` | Register with the bot |
| `/balance` | Check your point balance |
| `/history` | View your transaction history |

### Curator Commands
| Command | Description |
|---------|-------------|
| `/add @user amount note` | Add points to a player |
| `/subtract @user amount note` | Subtract points from a player |
| `/penalty @user amount note` | Apply a penalty |
| `/spend @user amount note` | Record point spending |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/users` | List all registered users |
| `/export` | Export all data as CSV |
| `/setrole @user role` | Change user role (player/curator/admin) |

## API Endpoints

### Transactions
- `POST /transactions/add`
- `POST /transactions/subtract`
- `POST /transactions/penalty`
- `POST /transactions/spend`

### Players
- `GET /players/{id}/balance`
- `GET /players/{id}/history`

### Admin
- `GET /users`
- `POST /users`
- `POST /users/ensure`
- `GET /users/by-telegram/{telegram_id}`
- `GET /users/by-username/{username}`
- `GET /export`

### System
- `GET /health`

## Project Structure

```
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial.py
│   └── app/
│       ├── main.py
│       ├── core/
│       │   └── config.py
│       ├── db/
│       │   └── session.py
│       ├── models/
│       │   ├── base.py
│       │   ├── user.py
│       │   ├── transaction.py
│       │   └── balance.py
│       ├── schemas/
│       │   └── schemas.py
│       ├── services/
│       │   ├── user_service.py
│       │   └── transaction_service.py
│       └── api/
│           └── routes/
│               ├── transactions.py
│               ├── players.py
│               └── admin.py
├── bot/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── __main__.py
│   ├── bot.py
│   ├── config.py
│   ├── handlers/
│   │   ├── common.py
│   │   ├── player.py
│   │   ├── curator.py
│   │   └── admin.py
│   └── services/
│       └── api_client.py
├── docker-compose.yml
├── .env.example
└── README.md
```

## Core Safety Features

- **Decimal precision** for all financial values (18,2)
- **Database transactions** for every balance update
- **SELECT FOR UPDATE** row-level locking prevents race conditions
- **Idempotency** via unique `request_id` prevents duplicate transactions
- **Role-based access control** (player / curator / admin)
- **Negative balance prevention** on debit operations
- **Structured logging** for all requests, transactions, and errors
- **Atomic operations** — if any step fails, the entire transaction rolls back

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `POSTGRES_USER` | DB user for container |
| `POSTGRES_PASSWORD` | DB password for container |
| `POSTGRES_DB` | DB name for container |
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `SECRET_KEY` | Application secret key |
| `BACKEND_URL` | Backend URL (default: http://backend:8000) |
| `ENV` | Environment (production/development) |
