# Noor AI — System Architecture

## High-Level Architecture

```
                    ┌─────────────────┐
                    │   Syrian Users   │
                    │  (Merchants &    │
                    │   Customers)     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   WhatsApp /     │
                    │   Telegram       │
                    └────────┬────────┘
                             │ Webhooks
                    ┌────────┴────────┐
                    │   FastAPI        │
                    │   Gateway        │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Agent Router    │
                    │  (NLP Intent     │
                    │   Detection)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴──────┐ ┌────┴────┐ ┌──────┴───────┐
     │ Order Agent   │ │CRM Agent│ │Inventory Agent│
     └────────┬──────┘ └────┬────┘ └──────┬───────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────┐
                    │   Claude API     │
                    │  (Complex NLU)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴──────┐ ┌────┴────┐ ┌──────┴───────┐
     │  PostgreSQL   │ │  Redis  │ │   Celery     │
     │  (Data)       │ │ (Cache) │ │  (Tasks)     │
     └───────────────┘ └─────────┘ └──────────────┘
```

## Component Details

### 1. API Gateway (FastAPI)
- **Role**: Receives webhooks from WhatsApp/Telegram, routes to agents
- **Endpoints**:
  - `GET /health` — Health check
  - `GET /webhook/whatsapp` — WhatsApp verification
  - `POST /webhook/whatsapp` — Incoming WhatsApp messages
  - `POST /webhook/telegram` — Incoming Telegram messages
  - `POST /api/merchants/` — Merchant registration
  - `GET /api/merchants/{id}` — Merchant details

### 2. Agent Router
- **Role**: Analyzes incoming message, detects intent, routes to correct agent
- **Flow**:
  1. Receive raw message text
  2. Run through Syrian Arabic NLP (normalize, detect intent)
  3. Look up merchant/customer context from DB
  4. Route to specialized agent based on intent
  5. Return agent response to gateway for sending

### 3. Specialized Agents

#### Order Agent
- Creates new orders from chat messages
- Tracks order status (pending → confirmed → preparing → ready → delivered)
- Handles cancellations
- Uses Claude API for complex order parsing

#### CRM Agent
- Creates customer profiles automatically
- Recognizes returning customers
- Personalizes greetings based on order history
- Identifies VIP customers

#### Inventory Agent
- Manages product catalog
- Tracks stock quantities
- Sends low-stock alerts
- Generates inventory reports

### 4. NLP Pipeline
- **Step 1**: Text normalization (diacritics, character variants)
- **Step 2**: Intent detection (keyword matching for speed)
- **Step 3**: Entity extraction (quantities, phone numbers, product names)
- **Step 4**: If low confidence → Claude API for understanding
- **Language support**: Syrian Arabic dialect, MSA, English

### 5. Data Layer

#### PostgreSQL Tables
- `merchants` — Business owners and their settings
- `customers` — End customers of each merchant
- `orders` — Order records with status tracking
- `order_items` — Line items in each order
- `products` — Product catalog per merchant

#### Redis
- Conversation sessions (TTL: 30 minutes)
- Rate limiting counters
- Cached merchant data

### 6. External Integrations
- **WhatsApp Business API** — Send/receive messages, interactive elements
- **Telegram Bot API** — Send/receive messages, inline keyboards
- **Claude API** — Complex language understanding, response generation
- **SyriaTel Cash API** — Payment processing (Phase 2)
- **MTN Cash API** — Payment processing (Phase 2)

## Message Flow (Example: New Order)

```
1. Customer sends "بدي اطلب شاورما" on WhatsApp
2. WhatsApp → POST /webhook/whatsapp
3. Gateway extracts phone + message text
4. Router runs NLP: intent="new_order", confidence=0.9
5. Router sends to OrderAgent
6. OrderAgent loads merchant's product catalog from DB
7. OrderAgent calls Claude: "Customer wants shawarma, here's the menu..."
8. Claude responds with order confirmation in Syrian Arabic
9. OrderAgent creates Order record in PostgreSQL
10. Gateway sends response via WhatsApp API
11. Customer sees: "تكرم! طلبيتك: شاورما دجاج ١ - المجموع ٢٥٠٠٠ ل.س"
```

## Security Considerations
- WhatsApp webhook verification token
- Rate limiting per phone number (Redis)
- Input sanitization for all user messages
- No PII in logs
- Encrypted database connections
- API key rotation schedule
- HTTPS only

## Scalability Plan
- **Phase 1** (100 merchants): Single server, vertical scaling
- **Phase 2** (1K merchants): Horizontal scaling, load balancer
- **Phase 3** (10K merchants): Microservices, message queue, read replicas
