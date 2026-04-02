"""Multi-language response templates.

Provides canned responses in Syrian Arabic, MSA, and English
so the bot can respond in the customer's preferred language.
"""

TEMPLATES = {
    "welcome": {
        "ar-SY": "أهلا وسهلا! أنا نور، مساعدك الذكي. كيف بقدر ساعدك؟",
        "ar": "مرحباً! أنا نور، مساعدك الذكي. كيف يمكنني مساعدتك؟",
        "en": "Welcome! I'm Noor, your smart assistant. How can I help you?",
    },
    "order_confirmed": {
        "ar-SY": "تم تأكيد طلبيتك #{order_id}! المجموع: {total} ل.س ✅",
        "ar": "تم تأكيد طلبك #{order_id}! المجموع: {total} ل.س ✅",
        "en": "Order #{order_id} confirmed! Total: {total} SYP ✅",
    },
    "order_preparing": {
        "ar-SY": "طلبيتك #{order_id} قيد التحضير. رح تكون جاهزة قريباً!",
        "ar": "طلبك #{order_id} قيد التحضير. سيكون جاهزاً قريباً!",
        "en": "Order #{order_id} is being prepared. It will be ready soon!",
    },
    "order_ready": {
        "ar-SY": "طلبيتك #{order_id} جاهزة! 🎉 تفضل استلمها.",
        "ar": "طلبك #{order_id} جاهز! 🎉 تفضل باستلامه.",
        "en": "Order #{order_id} is ready! 🎉 Please pick it up.",
    },
    "order_delivered": {
        "ar-SY": "تم توصيل طلبيتك #{order_id}! شكراً إلك 🙏",
        "ar": "تم توصيل طلبك #{order_id}! شكراً لك 🙏",
        "en": "Order #{order_id} has been delivered! Thank you 🙏",
    },
    "order_cancelled": {
        "ar-SY": "تم إلغاء طلبيتك #{order_id}. إذا بدك تطلب شي تاني، نحنا هون!",
        "ar": "تم إلغاء طلبك #{order_id}. إذا أردت طلب شيء آخر، نحن هنا!",
        "en": "Order #{order_id} has been cancelled. If you'd like to order something else, we're here!",
    },
    "payment_received": {
        "ar-SY": "تم استلام الدفعة بنجاح! شكراً 💚",
        "ar": "تم استلام الدفعة بنجاح! شكراً 💚",
        "en": "Payment received successfully! Thank you 💚",
    },
    "low_stock_alert": {
        "ar-SY": "⚠️ تنبيه: {product} — باقي {stock} حبات فقط!",
        "ar": "⚠️ تنبيه: {product} — متبقي {stock} فقط!",
        "en": "⚠️ Alert: {product} — only {stock} left!",
    },
    "not_understood": {
        "ar-SY": "ما فهمت عليك. ممكن توضحلي أكتر شو بدك؟",
        "ar": "لم أفهم. هل يمكنك التوضيح أكثر؟",
        "en": "I didn't understand. Could you please clarify?",
    },
    "goodbye": {
        "ar-SY": "شكراً إلك! إذا بدك شي تاني، ابعتلي. مع السلامة! 👋",
        "ar": "شكراً لك! إذا احتجت شيئاً آخر، راسلني. مع السلامة! 👋",
        "en": "Thank you! If you need anything else, message me. Goodbye! 👋",
    },
    "ask_review": {
        "ar-SY": "كيف كانت تجربتك؟ قيّمنا من 1 لـ 5 ⭐",
        "ar": "كيف كانت تجربتك؟ قيّمنا من 1 إلى 5 ⭐",
        "en": "How was your experience? Rate us from 1 to 5 ⭐",
    },
    "loyalty_earned": {
        "ar-SY": "🎯 كسبت {points} نقطة ولاء! رصيدك: {total} نقطة",
        "ar": "🎯 كسبت {points} نقطة ولاء! رصيدك: {total} نقطة",
        "en": "🎯 You earned {points} loyalty points! Balance: {total} points",
    },
}


def get_template(key: str, language: str = "ar-SY", **kwargs) -> str:
    """Get a response template in the specified language."""
    template_group = TEMPLATES.get(key, {})
    template = template_group.get(language, template_group.get("ar-SY", ""))

    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    return template


def get_available_languages() -> list[dict]:
    """List available languages."""
    return [
        {"code": "ar-SY", "name": "عربي سوري", "name_en": "Syrian Arabic"},
        {"code": "ar", "name": "عربي فصحى", "name_en": "Modern Standard Arabic"},
        {"code": "en", "name": "English", "name_en": "English"},
    ]
