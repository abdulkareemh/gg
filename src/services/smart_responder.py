"""Rule-based smart responder.

Handles 80%+ of messages WITHOUT calling Claude API.
Only falls back to Claude for complex/ambiguous messages.

This eliminates the Claude API as a hard dependency for most interactions.
"""

from src.nlp.syrian_arabic import detect_intent, normalize_arabic, extract_quantity
from src.nlp.fuzzy_search import fuzzy_match_product
from src.nlp.arabic_numbers import parse_quantity_and_item
from src.services.response_cache import cached_intent, cache_intent, cached_response, cache_response
from src.services.auto_reply import get_auto_reply


class SmartResponder:
    """Handles messages using rules + cache before falling back to Claude."""

    def __init__(self):
        self.greetings = {
            "مرحبا", "هلا", "اهلا", "السلام عليكم", "صباح الخير",
            "مساء الخير", "هاي", "hi", "hello", "hey",
        }
        self.thank_words = {"شكرا", "شكراً", "يسلمو", "thanks", "thank you", "مشكور"}
        self.bye_words = {"باي", "مع السلامه", "الله معك", "bye", "goodbye"}

    def try_respond(
        self,
        message: str,
        merchant_context: dict,
        products: list[dict] | None = None,
    ) -> tuple[str | None, str | None, bool]:
        """Try to respond without Claude API.

        Returns: (response_text, action, was_handled)
        If was_handled is False, caller should fall back to Claude.
        """
        normalized = normalize_arabic(message.lower().strip())

        # 1. Check response cache
        merchant_id = merchant_context.get("id", 0)
        cached = cached_response(merchant_id, message)
        if cached:
            return cached, "cached", True

        # 2. Simple greetings
        if normalized in self.greetings or any(g in normalized for g in self.greetings):
            name = merchant_context.get("business_name", "")
            resp = (
                f"أهلا وسهلا فيك بـ{name}! 🌟\n\n"
                f"كيف بقدر ساعدك؟\n"
                f"• ابعت 'القائمة' لتشوف الأصناف\n"
                f"• ابعت 'بدي اطلب' للطلب"
            )
            cache_response(merchant_id, message, resp)
            return resp, "greeting", True

        # 3. Thank you
        if normalized in self.thank_words or any(w in normalized for w in self.thank_words):
            return "العفو! إذا بدك شي تاني، ابعتلي 🙏", "thanks", True

        # 4. Goodbye
        if normalized in self.bye_words or any(w in normalized for w in self.bye_words):
            return "مع السلامة! منتمنى نشوفك عنّا كمان مرة 👋", "goodbye", True

        # 5. FAQ auto-reply
        auto = get_auto_reply(message, merchant_context)
        if auto:
            cache_response(merchant_id, message, auto)
            return auto, "faq", True

        # 6. Menu request
        if any(w in normalized for w in ["القائمه", "القايمه", "المنيو", "menu", "الاصناف", "المنتجات"]):
            if products:
                from src.nlp.conversation import format_product_menu
                menu = format_product_menu([
                    {"name_ar": p.get("name_ar", ""), "price": p.get("price", 0),
                     "stock": p.get("stock", 0), "category": p.get("category", "")}
                    for p in products
                ])
                return menu, "menu", True
            return "ابعتلي 'بدي اطلب' وبعرضلك القائمة!", "menu_prompt", True

        # 7. Product search (if products available)
        if products:
            matches = fuzzy_match_product(message, products, threshold=0.5)
            if matches:
                qty, _ = parse_quantity_and_item(message)
                p = matches[0]
                total = qty * p["price"]
                resp = (
                    f"✅ {p['name_ar']} — {p['price']:,.0f} ل.س\n"
                    f"الكمية: {qty}\n"
                    f"المجموع: {total:,.0f} ل.س\n\n"
                    f"بدك تأكد الطلب؟"
                )
                return resp, "product_found", True

        # 8. Cached intent detection
        cached_int = cached_intent(message)
        if cached_int:
            intent, conf = cached_int
            if intent == "help":
                return self._help_message(), "help", True

        # 9. Intent detection (fast, no API)
        intent, confidence = detect_intent(message)
        cache_intent(message, intent, confidence)

        if intent == "help":
            return self._help_message(), "help", True

        # 10. If confidence is high enough for known intents, handle them
        if confidence >= 0.3 and intent in ("view_products", "new_order"):
            return "شو بدك تطلب؟ ابعتلي اسم المنتج أو 'القائمة' لتشوف الأصناف 📋", "order_prompt", True

        if confidence >= 0.3 and intent == "cancel_order":
            return "تم طلب الإلغاء. رح نتواصل معك للتأكيد.", "cancel_request", True

        # Can't handle — fall back to Claude
        return None, None, False

    def _help_message(self) -> str:
        return (
            "أهلا! أنا نور، مساعدك الذكي 🤖\n\n"
            "بقدر ساعدك بـ:\n"
            "📋 القائمة — عرض المنتجات\n"
            "📦 بدي اطلب — طلبية جديدة\n"
            "🔍 وين طلبيتي — تتبع الطلب\n"
            "❌ الغي — إلغاء الطلب\n"
            "🕐 ساعات العمل\n"
            "💳 طرق الدفع"
        )
