# Noor AI (نور) - AI Business Assistant for Syria

> Empowering Syrian SMEs with AI-powered conversational business tools

## Vision

Noor AI is the first AI-powered business assistant built specifically for the Syrian market. We help small and medium businesses manage their operations through conversational AI agents on WhatsApp and Telegram — in Syrian Arabic dialect.

## The Problem

- **500K+ Syrian SMEs** have no affordable digital tools
- Existing solutions don't support **Syrian Arabic dialect**
- Business owners manage everything via **WhatsApp/Telegram** manually
- **No inventory, order, or customer management** systems accessible to small shops
- The **diaspora** (8M+ Syrians abroad) struggle to transact with local businesses

## The Solution

Noor AI provides intelligent chatbot agents that plug into WhatsApp and Telegram to help businesses:

- **Order Management** — Receive, track, and fulfill orders via chat
- **Customer CRM** — Automatically track customer preferences and history
- **Inventory Tracking** — Real-time stock management with low-stock alerts
- **Payment Processing** — Integration with local payment methods (SyriaTel Cash, MTN Cash, bank transfers)
- **Multilingual Support** — Syrian Arabic dialect, Modern Standard Arabic, English
- **Analytics Dashboard** — Business insights and reports via simple chat commands
- **Diaspora Bridge** — Enable Syrians abroad to order/send gifts to family in Syria

## Tech Stack

- **Backend**: Python (FastAPI)
- **AI/NLP**: Custom Syrian Arabic NLP pipeline + Claude API for agent intelligence
- **Messaging**: WhatsApp Business API, Telegram Bot API
- **Database**: PostgreSQL + Redis
- **Infrastructure**: Docker, deployed on regional cloud
- **Payments**: Integration with Syrian mobile money providers

## Team

| Role | Responsibility |
|------|---------------|
| **CEO / Product** | Strategy, market fit, partnerships |
| **CTO / AI Lead** | Architecture, AI agents, NLP pipeline |
| **Backend Engineer** | API, database, integrations |
| **NLP Engineer** | Syrian Arabic dialect processing |
| **Growth Lead** | Go-to-market, merchant onboarding |
| **Designer** | UX for dashboard and chat flows |

## Project Structure

```
noor-ai/
├── src/
│   ├── agents/          # AI agent logic (order, crm, inventory)
│   ├── api/             # FastAPI endpoints
│   ├── nlp/             # Syrian Arabic NLP pipeline
│   ├── integrations/    # WhatsApp, Telegram, payment providers
│   ├── models/          # Database models
│   └── utils/           # Shared utilities
├── tests/               # Test suite
├── docs/                # Documentation
├── config/              # Configuration files
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Business Model

| Revenue Stream | Description |
|---------------|-------------|
| **SaaS Subscription** | Monthly plans: Free (50 orders/mo), Basic ($10), Pro ($30), Enterprise ($100) |
| **Transaction Fee** | 1.5% on payments processed through the platform |
| **Diaspora Premium** | Premium features for cross-border orders |

## Roadmap

### Phase 1 — MVP (Q2 2026)
- WhatsApp bot with order management
- Basic Syrian Arabic NLP
- Manual merchant onboarding

### Phase 2 — Growth (Q3 2026)
- Telegram integration
- Inventory management
- Payment processing
- Analytics dashboard

### Phase 3 — Scale (Q4 2026)
- Diaspora bridge features
- Multi-city expansion
- Marketplace features
- API for third-party integrations

## Getting Started

```bash
# Clone the repository
git clone https://github.com/abdulkareemh/gg.git
cd gg

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp config/.env.example config/.env

# Run the application
python -m src.api.main

# Run tests
pytest tests/
```

## License

MIT License - Copyright (c) 2026 Noor AI
