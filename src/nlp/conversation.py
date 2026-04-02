"""Conversation context builder for Claude API calls.

Builds rich prompts with conversation history, merchant context,
and product catalog so Claude can give intelligent responses.
"""

from src.nlp.syrian_arabic import is_arabic


NOOR_SYSTEM_PROMPT = """أنت نور (Noor)، مساعد ذكي للأعمال التجارية في سوريا.

## شخصيتك:
- ودود ومحترف
- تتكلم باللهجة السورية
- مختصر وواضح
- تستخدم تعابير سورية مثل "تكرم"، "على راسي"، "إن شاء الله"

## قدراتك:
- إدارة الطلبيات (استقبال، تتبع، إلغاء)
- إدارة الزبائن (ملفات، سجل طلبات)
- إدارة المخزون (كميات، تنبيهات)
- تقارير يومية وأسبوعية

## قواعد:
- دائماً جاوب بالعربي السوري إلا إذا الزبون حكا بالإنجليزي
- لا تخترع أسعار — استخدم فقط الأسعار المعطاة
- إذا ما فهمت، اسأل بأدب
- المبالغ بالليرة السورية (ل.س)
"""


def build_conversation_prompt(
    merchant_name: str,
    products: list[dict],
    history: list[dict],
    customer_name: str | None = None,
) -> list[dict]:
    """Build a conversation prompt for Claude with full context.

    Returns a messages list ready for the Claude API.
    """
    # Build product catalog string
    if products:
        catalog = "المنتجات المتوفرة:\n"
        for p in products:
            stock_str = f" ({p.get('stock', '?')} متوفر)" if 'stock' in p else ""
            catalog += f"- {p['name_ar']}: {p['price']:,.0f} ل.س{stock_str}\n"
    else:
        catalog = "لا توجد منتجات مسجلة بعد."

    # Build context message
    context_parts = [
        f"المحل: {merchant_name}",
        catalog,
    ]
    if customer_name:
        context_parts.insert(1, f"الزبون: {customer_name}")

    context_message = "\n".join(context_parts)

    # Build messages list
    messages = [
        {"role": "user", "content": f"[سياق النظام]\n{context_message}"},
        {"role": "assistant", "content": "فهمت. جاهز لمساعدة الزبون."},
    ]

    # Add conversation history
    for msg in history[-8:]:  # Last 8 messages for context
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["text"]})

    return messages


def format_order_summary(items: list[dict]) -> str:
    """Format a cart/order into a readable Arabic summary."""
    if not items:
        return "السلة فاضية"

    lines = []
    total = 0
    for item in items:
        line_total = item["quantity"] * item["price"]
        total += line_total
        lines.append(f"  {item['name_ar']} × {item['quantity']} = {line_total:,.0f} ل.س")

    summary = "🛒 طلبيتك:\n" + "\n".join(lines)
    summary += f"\n\n💰 المجموع: {total:,.0f} ل.س"
    return summary


def format_product_menu(products: list[dict], category: str | None = None) -> str:
    """Format products into a readable Arabic menu."""
    if not products:
        return "ما في منتجات مسجلة بعد. ابعت 'إضافة منتج' لتبدأ."

    header = f"📋 قائمة {category}:" if category else "📋 القائمة:"
    lines = [header]

    current_cat = None
    for p in products:
        cat = p.get("category", "عام")
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n*{cat}*")

        stock_emoji = "✅" if p.get("stock", 0) > 0 else "❌"
        lines.append(f"  {stock_emoji} {p['name_ar']} — {p['price']:,.0f} ل.س")

    return "\n".join(lines)
