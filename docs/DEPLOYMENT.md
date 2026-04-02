# Noor AI — Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Redis 7+
- Docker (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/abdulkareemh/gg.git
cd gg

# Set up environment
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f app
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL
createdb noor_ai

# Set up environment
cp config/.env.example config/.env
# Edit config/.env with your database URL and API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests

```bash
# Install test dependencies
pip install aiosqlite

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_nlp.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Production Deployment

### Server Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB minimum
- **Storage**: 20GB SSD
- **OS**: Ubuntu 22.04 LTS

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_ENV` | Yes | `production` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `WHATSAPP_ACCESS_TOKEN` | Yes | WhatsApp Business API token |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | WhatsApp phone number ID |
| `WHATSAPP_VERIFY_TOKEN` | Yes | Webhook verification token |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token (if using Telegram) |
| `SYRIATEL_CASH_API_KEY` | No | SyriaTel Cash API key |
| `MTN_CASH_API_KEY` | No | MTN Cash API key |
| `APP_URL` | Yes | Public URL for callbacks |

### Docker Production Build

```bash
# Build production image
docker build -t noor-ai:latest .

# Run with production settings
docker run -d \
  --name noor-ai \
  -p 8000:8000 \
  --env-file config/.env \
  --restart unless-stopped \
  noor-ai:latest
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.noor-ai.sy;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.noor-ai.sy
```

### Database Backup

```bash
# Daily backup cron job
0 2 * * * pg_dump -U noor noor_ai | gzip > /backups/noor_ai_$(date +\%Y\%m\%d).sql.gz

# Restore from backup
gunzip -c backup.sql.gz | psql -U noor noor_ai
```

---

## WhatsApp Setup

### 1. Create Meta Business Account
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app (Business type)
3. Add WhatsApp product

### 2. Configure Webhook
1. In WhatsApp settings, go to Configuration
2. Set webhook URL: `https://api.noor-ai.sy/webhook/whatsapp`
3. Set verify token (same as `WHATSAPP_VERIFY_TOKEN` in .env)
4. Subscribe to `messages` webhook field

### 3. Get Access Token
1. Go to WhatsApp > API Setup
2. Generate a permanent access token
3. Copy the Phone Number ID
4. Add both to your `.env` file

---

## Telegram Setup

### 1. Create Bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow prompts to name your bot
4. Save the bot token

### 2. Set Webhook
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://api.noor-ai.sy/webhook/telegram"}'
```

---

## Monitoring

### Health Check
```bash
# Simple health check
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

### Log Format (Production)
Logs are JSON-formatted in production:
```json
{
  "timestamp": "2026-04-02T10:30:00.000Z",
  "level": "INFO",
  "logger": "noor.webhook",
  "message": "Order #42 created",
  "merchant_id": 1,
  "order_id": 42
}
```

### Uptime Monitoring
Set up a cron job or external service to ping `/health` every minute:
```bash
*/1 * * * * curl -sf http://localhost:8000/health > /dev/null || echo "Noor AI is down!" | mail -s "ALERT" admin@noor-ai.sy
```

---

## Scaling

### Phase 1 (100 merchants)
- Single server deployment
- PostgreSQL on same server
- Redis on same server

### Phase 2 (1,000 merchants)
- Separate database server
- Redis cluster
- Load balancer (nginx)
- 2 app instances

### Phase 3 (10,000+ merchants)
- Managed PostgreSQL (read replicas)
- Redis Cluster
- Kubernetes deployment
- CDN for static assets
- Message queue (RabbitMQ/Kafka)
