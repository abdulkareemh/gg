# Contributing to Noor AI

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/abdulkareemh/gg.git
cd gg

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Copy environment config
cp config/.env.example config/.env
```

## Code Style

- We use **ruff** for linting
- Follow PEP 8 conventions
- Use type hints for all function signatures
- All Arabic strings should use Syrian dialect where appropriate
- Comments in English, user-facing text in Arabic

```bash
# Run linter
ruff check src/ tests/

# Auto-fix
ruff check --fix src/ tests/
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_nlp.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Git Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Branch Naming
- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation
- `refactor/description` — Code refactoring

### Commit Messages
- Use imperative mood: "Add feature" not "Added feature"
- Keep first line under 70 characters
- Reference issue numbers: "Fix #42: resolve order tracking bug"

## Project Structure

```
src/
├── agents/         # AI agent logic
│   ├── base_agent.py      # Base class for all agents
│   ├── order_agent.py     # Order management
│   ├── crm_agent.py       # Customer relationships
│   ├── inventory_agent.py # Stock management
│   └── router.py          # Intent-based routing
├── api/            # FastAPI application
│   ├── main.py            # App entry point
│   ├── middleware.py       # Security middleware
│   ├── error_handler.py   # Global error handling
│   └── routes/            # API endpoints
├── integrations/   # External service clients
│   ├── whatsapp.py        # WhatsApp Business API
│   ├── telegram.py        # Telegram Bot API
│   └── payments.py        # Payment providers
├── models/         # SQLAlchemy models
├── nlp/            # Arabic NLP pipeline
│   ├── syrian_arabic.py   # Intent detection, normalization
│   ├── conversation.py    # Context builder for Claude
│   └── fuzzy_search.py    # Arabic fuzzy product search
├── services/       # Business logic layer
│   ├── merchant_service.py
│   ├── customer_service.py
│   ├── order_service.py
│   ├── product_service.py
│   ├── payment_service.py
│   ├── session_service.py
│   ├── notification_service.py
│   ├── message_handler.py
│   └── scheduler.py
└── utils/          # Shared utilities
    ├── config.py          # Settings management
    ├── logger.py          # Structured logging
    └── metrics.py         # Application metrics
```

## Adding a New Feature

### 1. New Agent Capability
1. Add intent keywords to `src/nlp/syrian_arabic.py`
2. Map intent to agent in `src/agents/router.py`
3. Implement handler in the appropriate agent
4. Add tests in `tests/`

### 2. New API Endpoint
1. Create route in `src/api/routes/`
2. Add service logic in `src/services/`
3. Register router in `src/api/main.py`
4. Document in `docs/API.md`
5. Add tests

### 3. New Integration
1. Create client in `src/integrations/`
2. Add config variables to `src/utils/config.py`
3. Update `config/.env.example`
4. Add tests with mocked HTTP calls
