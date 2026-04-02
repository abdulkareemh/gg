# Noor AI — Full Business Plan

## Executive Summary

**Noor AI (نور)** is an AI-powered business assistant built for the Syrian market. We provide WhatsApp and Telegram chatbot agents that help small and medium businesses (SMEs) manage their daily operations — orders, customers, inventory, and payments — entirely through conversational Arabic AI.

Syria's economy is in a reconstruction phase with 500K+ SMEs needing affordable digital tools. Our solution requires no app download, no training, and works on the platforms Syrians already use daily.

---

## Market Analysis

### Syria 2026 — Key Facts
- **Population**: ~22 million (including returnees)
- **GDP growth**: Accelerating with reconstruction efforts
- **Mobile penetration**: ~85% (primarily Android)
- **Internet access**: Expanding, primarily mobile data
- **Key messaging apps**: WhatsApp (80%+), Telegram (40%+)
- **Mobile money**: SyriaTel Cash, MTN Cash growing rapidly
- **Diaspora**: 8M+ Syrians abroad (Germany, Turkey, Lebanon, Jordan, Gulf)

### Target Segments
| Segment | Size | Pain Point | Willingness to Pay |
|---------|------|------------|-------------------|
| Restaurants & cafes | 80K+ | Order management chaos | High |
| Retail shops | 200K+ | No inventory tracking | Medium |
| Service providers | 100K+ | Appointment/booking management | Medium |
| Wholesalers | 30K+ | Order and delivery tracking | High |
| Home businesses | 100K+ | No online presence | Medium |

### Competitive Landscape
| Competitor | Weakness |
|-----------|----------|
| Generic chatbot builders | No Arabic dialect support, expensive |
| Shopify/WooCommerce | Requires website, English-first, too complex |
| Local POS systems | Hardware-dependent, expensive, no messaging |
| Manual WhatsApp groups | No automation, orders get lost |

**Our edge**: Only solution that combines Syrian Arabic NLP + WhatsApp-native + AI agents + local payment integration.

---

## Product Strategy

### Core Features (MVP — Q2 2026)

#### 1. Order Management Agent
- Receive orders via WhatsApp/Telegram chat
- Automatic order confirmation and tracking
- Status updates to customers (preparing, ready, delivered)
- Order history and repeat orders

#### 2. Customer CRM Agent
- Automatic customer profile creation from phone number
- Order history per customer
- VIP customer detection
- Personalized greetings and recommendations

#### 3. Inventory Agent
- Product catalog management via chat
- Stock tracking with low-stock alerts
- Price updates
- Category management

#### 4. Syrian Arabic NLP
- Intent detection for Syrian dialect
- Entity extraction (quantities, products, phone numbers)
- Text normalization for Arabic variants
- Multi-language support (Syrian Arabic, MSA, English)

### Phase 2 Features (Q3 2026)
- Payment processing (SyriaTel Cash, MTN Cash)
- Analytics and reporting via chat
- Telegram bot integration
- Multi-language menu generation

### Phase 3 Features (Q4 2026)
- Diaspora bridge (cross-border ordering)
- Web dashboard for advanced analytics
- Marketplace features
- API for third-party integrations
- Aleppo and multi-city expansion

---

## Technology Decisions

### Why Python + FastAPI?
- Fastest path to MVP
- Best AI/ML library ecosystem
- Async support for handling concurrent WhatsApp messages
- Easy to hire for

### Why Claude API for AI Agents?
- Best Arabic language understanding among LLMs
- Tool use capability for structured actions
- Cost-effective at scale (~$0.003 per interaction)
- Fast inference for real-time chat responses

### Why WhatsApp-First?
- 80%+ penetration in Syria
- No app download needed
- Business API supports rich interactions (lists, buttons)
- Trusted platform — users already transact via WhatsApp

### Architecture Decisions
| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Database | PostgreSQL | Reliable, handles Arabic text well, scalable |
| Cache | Redis | Session management, rate limiting |
| Task queue | Celery | Async processing for heavy operations |
| Deployment | Docker | Reproducible, easy to deploy on any cloud |
| NLP | Custom + Claude | Custom for speed (intents), Claude for complexity |

---

## Financial Projections

### Revenue Model
| Stream | Price | Year 1 Target |
|--------|-------|---------------|
| Free plan | $0 (50 orders/month) | 600 merchants |
| Basic plan | $10/month | 300 merchants |
| Pro plan | $30/month | 80 merchants |
| Enterprise | $100/month | 20 merchants |
| Transaction fees | 1.5% | $2K/month by Q4 |

### Year 1 Projections
| Quarter | Merchants | MRR | Cumulative Revenue |
|---------|-----------|-----|-------------------|
| Q2 2026 | 100 | $2K | $6K |
| Q3 2026 | 350 | $8K | $30K |
| Q4 2026 | 700 | $15K | $75K |
| Q1 2027 | 1,200 | $25K | $150K |

### Cost Structure (Monthly)
| Item | Cost |
|------|------|
| Team (5 people) | $15K |
| Cloud infrastructure | $500 |
| Claude API | $300 |
| WhatsApp Business API | $200 |
| Office (Damascus) | $300 |
| Marketing | $1K |
| **Total** | **$17.3K** |

### Funding
- **Pre-seed**: $500K (18-month runway)
- **Use of funds**: 70% team, 15% infrastructure, 10% marketing, 5% legal

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Internet instability | High | Medium | Offline-first design, message queuing |
| Payment regulation changes | Medium | High | Multi-provider strategy, compliance-first |
| WhatsApp API policy changes | Low | High | Telegram as backup, own app as Plan C |
| Slow merchant adoption | Medium | High | Free tier, in-person onboarding |
| Currency volatility (SYP) | High | Medium | USD pricing option, dynamic conversion |
| Competition from regional players | Low | Medium | Dialect moat, local relationships |

---

## Success Metrics (KPIs)

| Metric | Q2 Target | Q4 Target |
|--------|-----------|-----------|
| Active merchants | 100 | 700 |
| Monthly orders processed | 5K | 50K |
| Customer satisfaction (CSAT) | 4.0/5 | 4.5/5 |
| Merchant churn rate | <10% | <5% |
| Average response time | <3s | <2s |
| NLP accuracy | 80% | 92% |
| Revenue (MRR) | $2K | $15K |
