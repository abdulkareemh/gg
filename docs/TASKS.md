# Noor AI — Task Tracker

## Sprint 1 — Foundation (COMPLETED)

### Completed
- [x] **PROJ-001**: Initialize repository and project structure
- [x] **PROJ-002**: Create database models (Merchant, Customer, Order, Product, OrderItem)
- [x] **PROJ-003**: Set up FastAPI application with health check
- [x] **PROJ-004**: Build Syrian Arabic NLP pipeline (normalize, intent detect, entity extract)
- [x] **PROJ-005**: Design agent architecture (BaseAgent, Router)
- [x] **PROJ-006**: Implement OrderAgent with order CRUD flows
- [x] **PROJ-007**: Implement CRMAgent with customer recognition
- [x] **PROJ-008**: Implement InventoryAgent with stock management
- [x] **PROJ-009**: Create WhatsApp webhook endpoint (verify + receive)
- [x] **PROJ-010**: Create Telegram webhook endpoint
- [x] **PROJ-011**: Build WhatsApp client (send text, template, interactive)
- [x] **PROJ-012**: Build Telegram client (send text, inline keyboard, webhook)
- [x] **PROJ-013**: Write NLP unit tests
- [x] **PROJ-014**: Write agent routing tests
- [x] **PROJ-015**: Write API endpoint tests
- [x] **PROJ-016**: Docker and docker-compose setup
- [x] **PROJ-017**: Configuration management (.env, settings)
- [x] **PROJ-018**: Documentation (README, pitch, business plan, team)

---

## Current Sprint: Sprint 2 — Services & Database Layer

### Completed
- [x] **PROJ-019**: Connect OrderAgent to PostgreSQL — OrderService with full CRUD, daily summaries
- [x] **PROJ-020**: Connect CRMAgent to PostgreSQL — CustomerService with get_or_create, top customers, diaspora
- [x] **PROJ-021**: Connect InventoryAgent to PostgreSQL — ProductService with catalog, search, bulk import, low stock
- [x] **PROJ-022**: Implement Redis session store — SessionService with cart, history, state management
- [x] **PROJ-023**: Multi-turn conversation support — ConversationBuilder with history, context, Claude prompts
- [x] **PROJ-024**: WhatsApp/Telegram message sending — MessageHandler closes the full loop (receive → process → respond)
- [x] **PROJ-025**: Merchant self-registration flow via WhatsApp — multi-step onboarding (name, business, type, city)
- [x] **PROJ-027**: Order notification to merchant — NotificationService (new order, confirmed, ready, low stock, daily report)
- [x] **PROJ-028**: Session and conversation tests — test_session.py, test_conversation.py with mocked Redis
- [x] **PROJ-041**: Analytics endpoints — overview, top products, top customers
- [x] **PROJ-042**: MerchantService — phone lookup, create, update plan, deactivate
- [x] **PROJ-043**: Enhanced merchant API — full CRUD for products, orders, bulk import, low stock alerts
- [x] **PROJ-044**: Conversation context builder — Syrian Arabic system prompt, order summary formatter, menu formatter

---

## Sprint 3 — Security, Payments & Production (COMPLETED)

### Completed
- [x] **PROJ-029**: SyriaTel Cash payment integration — full provider with initiate, check, refund
- [x] **PROJ-030**: MTN Cash payment integration — full provider with initiate, check, refund
- [x] **PROJ-031**: Daily sales report generation — auto-sent via scheduler
- [x] **PROJ-032**: Low-stock alert scheduler — hourly checks with notifications
- [x] **PROJ-034**: Product search with fuzzy matching — Levenshtein distance + Arabic aliases
- [x] **PROJ-045**: Alembic database migrations — initial schema with all 6 tables
- [x] **PROJ-046**: Integration tests with SQLite — 15+ tests across all services
- [x] **PROJ-047**: Rate limiting middleware — 60 req/min per IP, X-RateLimit-Remaining header
- [x] **PROJ-048**: Webhook signature verification — HMAC SHA-256 WhatsApp validation
- [x] **PROJ-049**: Error handling middleware — global exception handler with Arabic error messages
- [x] **PROJ-050**: Logging and monitoring — structured JSON logging, in-memory metrics
- [x] **PROJ-051**: Payment Gateway — unified interface, auto-detect provider from phone prefix
- [x] **PROJ-052**: Payment webhook endpoints — SyriaTel and MTN callback handlers
- [x] **PROJ-053**: Payment model and service — DB persistence, callback handling
- [x] **PROJ-054**: CI/CD pipeline — GitHub Actions (lint, test, security scan, Docker build)
- [x] **PROJ-055**: CORS middleware — configured for dashboard and production domains
- [x] **PROJ-056**: Request size limiting — 1MB max body
- [x] **PROJ-057**: Request logging middleware — timing, status codes
- [x] **PROJ-058**: Metrics endpoint — /metrics with counters and timings
- [x] **PROJ-059**: Background task scheduler — periodic daily reports, stock checks, cleanup
- [x] **PROJ-060**: Fuzzy search tests, middleware tests, integration tests
- [x] **PROJ-061**: API documentation (docs/API.md)
- [x] **PROJ-062**: Deployment guide (docs/DEPLOYMENT.md)
- [x] **PROJ-063**: Chat flow documentation (docs/CHAT_FLOWS.md)
- [x] **PROJ-064**: Contributing guide (docs/CONTRIBUTING.md)

### Backlog (Sprint 4+)
- [ ] **PROJ-026**: Product catalog import (CSV upload via chat)
- [ ] **PROJ-033**: Customer order history lookup
- [ ] **PROJ-035**: Voice message transcription
- [ ] **PROJ-037**: Web dashboard (merchant analytics)
- [ ] **PROJ-038**: CI/CD pipeline setup
- [ ] **PROJ-039**: Production deployment
- [ ] **PROJ-040**: Security audit and penetration testing

---

## Decision Log

| Date | Decision | Reasoning | Owner |
|------|----------|-----------|-------|
| 2026-04-02 | Use Python + FastAPI | Best AI ecosystem, async support, fast MVP | CTO |
| 2026-04-02 | Claude API for agent intelligence | Best Arabic support, tool use, cost-effective | CTO |
| 2026-04-02 | WhatsApp-first strategy | 80%+ penetration in Syria, no app download | CEO |
| 2026-04-02 | Custom NLP + Claude hybrid | Custom for speed (intents), Claude for complex understanding | NLP Engineer |
| 2026-04-02 | PostgreSQL for database | Reliable, good Arabic text support, scalable | Backend Lead |
| 2026-04-02 | Docker for deployment | Reproducible, works on any cloud provider | CTO |
| 2026-04-02 | Free tier (50 orders/month) | Drive adoption, convert to paid with volume | CEO |
| 2026-04-02 | Damascus first, then Aleppo | Largest market, best infrastructure | CEO |
| 2026-04-02 | SYP pricing with USD option | Local market reality, diaspora needs USD | CEO |
| 2026-04-02 | Agent-based architecture | Modular, each agent specialized, easy to extend | CTO |

---

## Meetings & Notes

### 2026-04-02 — Kickoff
- **Attendees**: Full team
- **Decisions**:
  - Startup name: **Noor AI (نور)**
  - Target market: Syrian SMEs (restaurants, shops, services)
  - Platform: WhatsApp-first, Telegram second
  - Tech stack: Python, FastAPI, PostgreSQL, Claude API
  - MVP scope: Order management + CRM + Inventory via WhatsApp
  - Timeline: MVP in 10 weeks (by mid-June 2026)
  - Fundraising: $500K pre-seed target
- **Action items**:
  - CTO: Complete Sprint 1 (foundation) — DONE
  - CEO: Start merchant interviews in Damascus
  - Growth: Create social media presence
  - NLP: Collect Syrian Arabic conversation datasets
