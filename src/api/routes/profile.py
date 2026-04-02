"""Public merchant profile endpoints.

Generates shareable profile pages and links
that merchants can share with customers.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import get_db
from src.services.merchant_service import MerchantService
from src.services.product_service import ProductService
from src.services.review_service import ReviewService
from src.utils.qrcode import generate_whatsapp_link

router = APIRouter()


@router.get("/{merchant_id}", response_class=HTMLResponse)
async def merchant_profile_page(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Public merchant profile page — shareable link."""
    m_svc = MerchantService(db)
    merchant = await m_svc.get_by_id(merchant_id)

    if not merchant or not merchant.is_active:
        return HTMLResponse("<h1>المحل غير موجود</h1>", status_code=404)

    # Get products
    p_svc = ProductService(db)
    products = await p_svc.get_catalog(merchant_id)

    # Get rating
    r_svc = ReviewService(db)
    rating = await r_svc.get_merchant_rating(merchant_id)

    # Generate WhatsApp link
    wa_link = generate_whatsapp_link(merchant.phone, f"مرحبا، بدي اطلب من {merchant.business_name}")

    # Build product HTML
    products_html = ""
    current_cat = None
    for p in products:
        cat = p.category or "عام"
        if cat != current_cat:
            current_cat = cat
            products_html += f'<h3 style="color:#818cf8;margin:1.5rem 0 0.5rem;">{cat}</h3>'
        stock_dot = "🟢" if p.stock_quantity > 0 else "🔴"
        products_html += (
            f'<div style="display:flex;justify-content:space-between;padding:8px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<span>{stock_dot} {p.name_ar}</span>'
            f'<span style="color:#818cf8;">{float(p.price):,.0f} ل.س</span></div>'
        )

    stars = "⭐" * round(rating["average"]) if rating["average"] > 0 else ""
    rating_text = f'{rating["average"]}/5 ({rating["total_reviews"]} تقييم)' if rating["total_reviews"] > 0 else "جديد"

    type_labels = {"restaurant": "مطعم", "shop": "محل", "service": "خدمات"}
    type_label = type_labels.get(merchant.business_type, merchant.business_type)

    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{merchant.business_name} — نور AI</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'Segoe UI',Tahoma,sans-serif;background:#0f0f23;color:#e0e0e0;padding:0;}}
        .header{{background:linear-gradient(135deg,#1a1a3e,#0d0d2b);padding:2rem;text-align:center;}}
        .header h1{{font-size:1.8rem;color:#e0e0e0;margin-bottom:0.3rem;}}
        .header .type{{color:#818cf8;font-size:0.9rem;}}
        .header .city{{color:#8696a0;font-size:0.85rem;margin-top:0.3rem;}}
        .header .rating{{margin-top:0.5rem;font-size:0.9rem;}}
        .content{{max-width:600px;margin:0 auto;padding:1rem 1.5rem;}}
        .order-btn{{display:block;background:#00a884;color:white;text-align:center;
            padding:14px;border-radius:12px;font-size:1.1rem;font-weight:600;
            text-decoration:none;margin:1.5rem 0;}}
        .order-btn:hover{{background:#00c49a}}
        .section{{margin:1.5rem 0;}}
        .footer{{text-align:center;color:#64748b;padding:2rem;font-size:0.8rem;}}
    </style>
</head>
<body>
    <div class="header">
        <h1>{merchant.business_name}</h1>
        <div class="type">{type_label} — {merchant.city}</div>
        <div class="rating">{stars} {rating_text}</div>
    </div>
    <div class="content">
        <a href="{wa_link}" class="order-btn">اطلب الآن عبر واتساب 📱</a>
        <div class="section">
            <h2 style="margin-bottom:0.5rem;">📋 القائمة</h2>
            {products_html if products_html else '<p style="color:#8696a0;">لا توجد منتجات بعد</p>'}
        </div>
    </div>
    <div class="footer">
        مدعوم من نور AI 🌟<br>
        <a href="/" style="color:#818cf8;text-decoration:none;">noor-ai.sy</a>
    </div>
</body>
</html>"""

    return HTMLResponse(html)


@router.get("/{merchant_id}/json")
async def merchant_profile_json(merchant_id: int, db: AsyncSession = Depends(get_db)):
    """Public merchant profile as JSON (for mobile apps)."""
    m_svc = MerchantService(db)
    merchant = await m_svc.get_by_id(merchant_id)

    if not merchant or not merchant.is_active:
        return {"error": "Merchant not found"}

    p_svc = ProductService(db)
    products = await p_svc.get_catalog(merchant_id)

    r_svc = ReviewService(db)
    rating = await r_svc.get_merchant_rating(merchant_id)

    return {
        "business_name": merchant.business_name,
        "business_type": merchant.business_type,
        "city": merchant.city,
        "phone": merchant.phone,
        "rating": rating,
        "products": [
            {"name_ar": p.name_ar, "price": float(p.price), "category": p.category, "available": p.stock_quantity > 0}
            for p in products
        ],
        "whatsapp_link": generate_whatsapp_link(merchant.phone),
    }
