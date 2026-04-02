"""QR code generation for merchant sharing.

Generates WhatsApp/Telegram links as QR codes that customers
can scan to start chatting with a merchant's Noor AI bot.
"""


def generate_whatsapp_link(phone: str, message: str = "مرحبا") -> str:
    """Generate a WhatsApp click-to-chat link."""
    # Remove leading + and spaces
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    encoded_msg = message.replace(" ", "%20")
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"


def generate_telegram_link(bot_username: str) -> str:
    """Generate a Telegram bot link."""
    return f"https://t.me/{bot_username}"


def generate_share_text(merchant_name: str, phone: str, platform: str = "whatsapp") -> str:
    """Generate a shareable text with merchant info."""
    if platform == "whatsapp":
        link = generate_whatsapp_link(phone, f"مرحبا، بدي اطلب من {merchant_name}")
        return (
            f"🌟 اطلب من {merchant_name} عبر نور AI!\n"
            f"📱 اضغط الرابط وابدأ الطلب:\n"
            f"{link}"
        )
    else:
        return (
            f"🌟 اطلب من {merchant_name} عبر نور AI!\n"
            f"📱 تواصل معنا على الرقم: {phone}"
        )


def generate_merchant_card(merchant: dict) -> str:
    """Generate a text-based merchant business card."""
    lines = [
        f"╔══════════════════════════╗",
        f"║     🌟 {merchant['business_name']}     ║",
        f"╠══════════════════════════╣",
        f"║  📍 {merchant.get('city', '')}",
        f"║  📱 {merchant.get('phone', '')}",
        f"║  🏪 {merchant.get('business_type', '')}",
    ]

    if merchant.get("rating"):
        lines.append(f"║  ⭐ {merchant['rating']}/5")

    lines.extend([
        f"╠══════════════════════════╣",
        f"║  مدعوم من نور AI 🤖      ║",
        f"╚══════════════════════════╝",
    ])

    return "\n".join(lines)
