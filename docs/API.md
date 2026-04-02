# Noor AI — API Documentation

## Base URL
```
Production: https://api.noor-ai.sy
Development: http://localhost:8000
```

## Authentication
Currently using phone-based identification. API key authentication planned for Phase 2.

---

## Health & Monitoring

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "noor-ai",
  "version": "0.2.0"
}
```

### GET /metrics
Application metrics for monitoring.

**Response:**
```json
{
  "uptime_seconds": 3600,
  "counters": {
    "messages.total": 1523,
    "messages.whatsapp": 1200,
    "messages.telegram": 323,
    "orders.total": 89,
    "payments.syriatel_cash.success": 45
  },
  "timings": {
    "agent.order.response": {
      "avg_ms": 234.5,
      "count": 89,
      "min_ms": 120.0,
      "max_ms": 890.0
    }
  }
}
```

---

## Merchant Management

### POST /api/merchants/
Register a new merchant.

**Request:**
```json
{
  "phone": "+963944123456",
  "name": "أحمد",
  "business_name": "مطعم الشام",
  "business_type": "restaurant",
  "city": "دمشق",
  "language": "ar-SY",
  "platform": "whatsapp"
}
```

**Response (201):**
```json
{
  "status": "created",
  "message": "مرحبا أحمد! تم تسجيل مطعم الشام بنجاح.",
  "merchant_id": 1
}
```

**Errors:**
- `409` — Phone number already registered

### GET /api/merchants/{merchant_id}
Get merchant details.

**Response:**
```json
{
  "id": 1,
  "phone": "+963944123456",
  "name": "أحمد",
  "business_name": "مطعم الشام",
  "business_type": "restaurant",
  "city": "دمشق",
  "plan": "free",
  "is_active": true
}
```

---

## Products

### POST /api/merchants/{merchant_id}/products
Add a product to the catalog.

**Request:**
```json
{
  "name": "Shawarma",
  "name_ar": "شاورما دجاج",
  "price": 25000,
  "category": "ساندويشات",
  "stock_quantity": 50,
  "description": "شاورما دجاج مع ثوم وبطاطا"
}
```

**Response:**
```json
{
  "status": "created",
  "product_id": 1,
  "name_ar": "شاورما دجاج"
}
```

### POST /api/merchants/{merchant_id}/products/bulk
Bulk add products.

**Request:**
```json
{
  "products": [
    {"name": "Shawarma", "name_ar": "شاورما", "price": 25000},
    {"name": "Falafel", "name_ar": "فلافل", "price": 15000},
    {"name": "Juice", "name_ar": "عصير", "price": 5000}
  ]
}
```

**Response:**
```json
{
  "status": "created",
  "count": 3
}
```

### GET /api/merchants/{merchant_id}/products
List product catalog.

**Query Parameters:**
- `category` (optional) — Filter by category

**Response:**
```json
{
  "count": 3,
  "products": [
    {
      "id": 1,
      "name": "Shawarma",
      "name_ar": "شاورما دجاج",
      "price": 25000.0,
      "category": "ساندويشات",
      "stock": 50,
      "available": true
    }
  ]
}
```

### GET /api/merchants/{merchant_id}/products/low-stock
Get products with low stock.

**Response:**
```json
{
  "count": 2,
  "products": [
    {"id": 3, "name_ar": "عصير برتقال", "stock": 2, "threshold": 5}
  ]
}
```

---

## Orders

### GET /api/merchants/{merchant_id}/orders
List orders.

**Query Parameters:**
- `status` (optional) — Filter by status: `pending`, `confirmed`, `preparing`, `ready`, `delivered`, `completed`, `cancelled`

**Response:**
```json
{
  "count": 5,
  "orders": [
    {
      "id": 42,
      "customer_id": 7,
      "status": "preparing",
      "total": 55000.0,
      "payment_status": "paid",
      "created_at": "2026-04-02T10:30:00"
    }
  ]
}
```

### GET /api/merchants/{merchant_id}/orders/summary
Get today's order summary.

**Response:**
```json
{
  "order_count": 12,
  "total_revenue": 450000.0,
  "currency": "SYP"
}
```

### PATCH /api/merchants/{merchant_id}/orders/{order_id}/status
Update order status.

**Query Parameters:**
- `status` — New status value

**Response:**
```json
{
  "order_id": 42,
  "status": "ready"
}
```

---

## Analytics

### GET /api/merchants/{merchant_id}/analytics/overview
Business overview with weekly and monthly stats.

**Response:**
```json
{
  "weekly": {"orders": 45, "revenue": 1250000.0},
  "monthly": {"orders": 180, "revenue": 5400000.0},
  "total_customers": 89,
  "total_products": 24,
  "currency": "SYP"
}
```

### GET /api/merchants/{merchant_id}/analytics/top-products
Top selling products.

**Query Parameters:**
- `limit` (optional, default: 5)

**Response:**
```json
{
  "products": [
    {"name_ar": "شاورما دجاج", "total_sold": 156, "revenue": 3900000.0},
    {"name_ar": "فلافل", "total_sold": 98, "revenue": 1470000.0}
  ]
}
```

### GET /api/merchants/{merchant_id}/analytics/top-customers
Top customers by order count.

**Response:**
```json
{
  "customers": [
    {"name": "محمد", "phone": "+963955111111", "total_orders": 23}
  ]
}
```

---

## Webhooks

### GET /webhook/whatsapp
WhatsApp webhook verification.

### POST /webhook/whatsapp
Incoming WhatsApp messages.

### POST /webhook/telegram
Incoming Telegram messages.

### POST /webhook/payment/syriatel
SyriaTel Cash payment callback.

### POST /webhook/payment/mtn
MTN Cash payment callback.

---

## Rate Limiting

All endpoints are rate-limited to **60 requests per minute per IP**.

Response headers:
- `X-RateLimit-Remaining` — Requests remaining in current window
- `X-Response-Time` — Server response time

When rate limited, returns `429 Too Many Requests` with `Retry-After: 60` header.

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error description in English",
  "error_ar": "وصف الخطأ بالعربي"
}
```

| Status Code | Meaning |
|------------|---------|
| 400 | Bad request — invalid input |
| 401 | Unauthorized — invalid webhook signature |
| 403 | Forbidden — verification failed |
| 404 | Not found |
| 409 | Conflict — duplicate resource |
| 413 | Request body too large (>1MB) |
| 429 | Rate limited |
| 500 | Internal server error |
