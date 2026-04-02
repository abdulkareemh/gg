"""Demo chat simulator API.

Provides a web-based chat interface that simulates WhatsApp
conversations using the real Noor AI backend. No WhatsApp API needed.

Used for:
1. Pitching to merchants (show them the bot on your phone)
2. Development and testing
3. Investor demos
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.agents.router import AgentRouter
from src.nlp.syrian_arabic import detect_intent
from src.nlp.fuzzy_search import fuzzy_match_product
from src.nlp.conversation import format_order_summary, format_product_menu
from src.services.auto_reply import get_auto_reply

router = APIRouter()
agent_router = AgentRouter()

# In-memory demo state (per session)
DEMO_SESSIONS: dict[str, dict] = {}

# Demo restaurant data
DEMO_MERCHANT = {
    "id": 1,
    "name": "أبو خالد",
    "business_name": "مطعم أبو خالد",
    "city": "دمشق",
    "phone": "+963944100001",
    "opening_time": "09:00",
    "closing_time": "23:00",
}

DEMO_PRODUCTS = [
    {"id": 1, "name_ar": "شاورما دجاج", "name": "Chicken Shawarma", "price": 25000, "category": "ساندويشات", "stock": 50},
    {"id": 2, "name_ar": "شاورما لحمة", "name": "Meat Shawarma", "price": 35000, "category": "ساندويشات", "stock": 40},
    {"id": 3, "name_ar": "فلافل", "name": "Falafel", "price": 15000, "category": "ساندويشات", "stock": 60},
    {"id": 4, "name_ar": "حمص", "name": "Hummus", "price": 12000, "category": "مقبلات", "stock": 30},
    {"id": 5, "name_ar": "فتوش", "name": "Fattoush", "price": 12000, "category": "سلطات", "stock": 25},
    {"id": 6, "name_ar": "كبة مقلية", "name": "Fried Kibbeh", "price": 20000, "category": "أطباق رئيسية", "stock": 20},
    {"id": 7, "name_ar": "مشاوي مشكلة", "name": "Mixed Grill", "price": 65000, "category": "أطباق رئيسية", "stock": 10},
    {"id": 8, "name_ar": "عصير برتقال", "name": "Orange Juice", "price": 5000, "category": "مشروبات", "stock": 100},
    {"id": 9, "name_ar": "قهوة عربية", "name": "Arabic Coffee", "price": 3000, "category": "مشروبات", "stock": 200},
    {"id": 10, "name_ar": "كنافة", "name": "Kunafa", "price": 15000, "category": "حلويات", "stock": 20},
]


class ChatMessage(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    timestamp: str
    action: str | None = None
    data: dict | None = None


def _get_session(session_id: str) -> dict:
    if session_id not in DEMO_SESSIONS:
        DEMO_SESSIONS[session_id] = {
            "state": "idle",
            "cart": [],
            "history": [],
            "order_count": 0,
            "step": None,
        }
    return DEMO_SESSIONS[session_id]


def _process_demo_message(message: str, session: dict) -> tuple[str, str | None, dict | None]:
    """Process a message through the demo pipeline. Returns (reply, action, data)."""
    msg_lower = message.strip().lower()
    from src.nlp.syrian_arabic import normalize_arabic
    normalized = normalize_arabic(msg_lower)

    # Check if in ordering flow
    if session["state"] == "confirming":
        return _handle_confirm(message, session)

    # Intent detection first (so order tracking etc. is handled before FAQ)
    intent, confidence = detect_intent(message)

    # Check order status early (before auto-reply catches it)
    if intent == "check_order":
        if session["order_count"] > 0:
            return f"طلبيتك #{session['order_count']} قيد التحضير 🔄\nرح تكون جاهزة خلال 15-20 دقيقة!", "order_status", None
        return "ما لقيت طلبيات سابقة. بدك تطلب شي؟", "no_order", None

    # Auto-reply check for FAQ
    ctx = {**DEMO_MERCHANT, "address": "شارع الحمرا، المزة", "closed_days": "—"}
    auto = get_auto_reply(message, ctx)
    if auto:
        return auto, "auto_reply", None

    # Greeting
    if intent == "greeting":
        return (
            f"أهلا وسهلا فيك بمطعم أبو خالد! 🌟\n\n"
            f"كيف بقدر ساعدك؟\n"
            f"• ابعت 'القائمة' لتشوف الأصناف\n"
            f"• ابعت 'بدي اطلب' للطلب\n"
            f"• ابعت 'مساعدة' للمساعدة"
        ), "greeting", None

    # View menu
    if intent == "view_products" or "القائمة" in normalized or "المنيو" in normalized or "menu" in msg_lower:
        menu = format_product_menu(DEMO_PRODUCTS)
        return menu + "\n\nابعت اسم المنتج أو 'بدي اطلب' للطلب!", "show_menu", None

    # New order
    if intent == "new_order" or "اطلب" in normalized:
        # Check if specific products mentioned
        matches = fuzzy_match_product(message, DEMO_PRODUCTS, threshold=0.4)
        if matches:
            return _handle_product_selection(message, matches, session)

        return (
            "شو بدك تطلب؟ 📋\n\n"
            + "\n".join(f"  • {p['name_ar']} — {p['price']:,.0f} ل.س" for p in DEMO_PRODUCTS[:6])
            + "\n\nابعت اسم المنتج والكمية (مثلاً: 2 شاورما)"
        ), "ask_order", None

    # Cancel
    if intent == "cancel_order":
        if session["cart"]:
            session["cart"] = []
            session["state"] = "idle"
            return "تم إلغاء الطلبية ❌\nإذا بدك تطلب شي تاني، ابعتلي!", "cancelled", None
        return "ما في طلبية لإلغائها.", "no_order", None

    # Help
    if intent == "help":
        return (
            "أهلا! أنا نور، مساعدك الذكي 🤖\n\n"
            "بقدر ساعدك بـ:\n"
            "📋 القائمة — عرض المنتجات\n"
            "📦 بدي اطلب — طلبية جديدة\n"
            "🔍 وين طلبيتي — تتبع الطلب\n"
            "❌ الغي — إلغاء الطلب\n"
            "🕐 ساعات العمل — معلومات المحل\n"
            "💳 طرق الدفع — كيف تدفع"
        ), "help", None

    # Try fuzzy product match
    matches = fuzzy_match_product(message, DEMO_PRODUCTS, threshold=0.4)
    if matches:
        return _handle_product_selection(message, matches, session)

    # Fallback
    return "ما فهمت عليك 🤔\nابعت 'القائمة' لتشوف الأصناف أو 'مساعدة' للمساعدة.", "unknown", None


def _handle_product_selection(message: str, matches: list[dict], session: dict) -> tuple[str, str | None, dict | None]:
    """Handle when a product name is detected."""
    from src.nlp.arabic_numbers import parse_quantity_and_item
    qty, _ = parse_quantity_and_item(message)

    product = matches[0]  # Best match
    total = qty * product["price"]

    # Add to cart
    cart_item = None
    for item in session["cart"]:
        if item["id"] == product["id"]:
            item["quantity"] += qty
            item["total"] = item["quantity"] * item["price"]
            cart_item = item
            break

    if not cart_item:
        cart_item = {
            "id": product["id"],
            "name_ar": product["name_ar"],
            "quantity": qty,
            "price": product["price"],
            "total": total,
        }
        session["cart"].append(cart_item)

    # Show cart summary
    cart_total = sum(i["total"] for i in session["cart"])
    cart_lines = [f"  • {i['name_ar']} × {i['quantity']} = {i['total']:,.0f} ل.س" for i in session["cart"]]

    session["state"] = "confirming"

    return (
        f"تمام! تمت الإضافة ✅\n\n"
        f"🛒 سلّتك:\n" + "\n".join(cart_lines) +
        f"\n\n💰 المجموع: {cart_total:,.0f} ل.س\n\n"
        f"• ابعت اسم منتج تاني لإضافته\n"
        f"• ابعت 'تأكيد' لتأكيد الطلب\n"
        f"• ابعت 'الغي' للإلغاء"
    ), "item_added", {"cart": session["cart"]}


def _handle_confirm(message: str, session: dict) -> tuple[str, str | None, dict | None]:
    """Handle confirmation step."""
    from src.nlp.syrian_arabic import normalize_arabic
    normalized = normalize_arabic(message.lower())
    confirm_words = ["تأكيد", "تمام", "اي", "نعم", "اكيد", "yes", "ok", "confirm"]
    cancel_words = ["الغي", "لا", "كنسل", "cancel", "no"]

    if any(w in normalized for w in cancel_words):
        session["cart"] = []
        session["state"] = "idle"
        return "تم إلغاء الطلبية ❌\nإذا بدك شي تاني، ابعتلي!", "cancelled", None

    if any(w in normalized for w in confirm_words):
        cart_total = sum(i["total"] for i in session["cart"])
        session["order_count"] += 1
        order_id = session["order_count"]

        cart_lines = [f"  • {i['name_ar']} × {i['quantity']}" for i in session["cart"]]
        receipt = (
            f"✅ تم تأكيد طلبيتك #{order_id}!\n\n"
            + "\n".join(cart_lines) +
            f"\n\n💰 المجموع: {cart_total:,.0f} ل.س\n"
            f"⏱️ الوقت المتوقع: 15-20 دقيقة\n\n"
            f"رح نبعتلك تحديث لما تصير جاهزة! 🙏\n\n"
            f"كيف بدك تدفع؟\n"
            f"1. كاش عند الاستلام\n"
            f"2. سيرياتيل كاش\n"
            f"3. MTN كاش"
        )

        session["cart"] = []
        session["state"] = "idle"
        return receipt, "order_confirmed", {"order_id": order_id, "total": cart_total}

    # Maybe they're adding more items
    matches = fuzzy_match_product(message, DEMO_PRODUCTS, threshold=0.4)
    if matches:
        return _handle_product_selection(message, matches, session)

    return "ابعت 'تأكيد' لتأكيد الطلب، أو ابعت اسم منتج تاني لإضافته.", "waiting_confirm", None


# --- API Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def demo_chat(msg: ChatMessage):
    """Send a message to the demo bot and get a response."""
    session = _get_session(msg.session_id)
    session["history"].append({"role": "user", "text": msg.message, "time": datetime.utcnow().isoformat()})

    reply, action, data = _process_demo_message(msg.message, session)

    session["history"].append({"role": "bot", "text": reply, "time": datetime.utcnow().isoformat()})

    return ChatResponse(
        reply=reply,
        timestamp=datetime.utcnow().isoformat(),
        action=action,
        data=data,
    )


@router.get("/products")
async def demo_products():
    """Get demo product list."""
    return {"products": DEMO_PRODUCTS}


@router.post("/reset")
async def demo_reset(session_id: str = "default"):
    """Reset a demo session."""
    if session_id in DEMO_SESSIONS:
        del DEMO_SESSIONS[session_id]
    return {"status": "reset", "session_id": session_id}


@router.get("/info")
async def demo_info():
    """Get demo merchant info."""
    return {
        "merchant": DEMO_MERCHANT,
        "product_count": len(DEMO_PRODUCTS),
        "features": [
            "طلبيات عبر المحادثة",
            "بحث ذكي عن المنتجات",
            "سلة تسوق",
            "تأكيد وإلغاء الطلبات",
            "أسئلة شائعة تلقائية",
            "باللهجة السورية",
        ],
    }
