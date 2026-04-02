"""Business hours enforcement for message handling."""

from datetime import datetime


DAYS_AR = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

DAYS_EN = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

# Syria timezone offset (UTC+3)
SYRIA_UTC_OFFSET = 3


def get_syria_time() -> datetime:
    """Get current time in Syria (UTC+3)."""
    from datetime import timedelta
    return datetime.utcnow() + timedelta(hours=SYRIA_UTC_OFFSET)


def is_within_hours(opening: str, closing: str) -> bool:
    """Check if current Syria time is within business hours."""
    now = get_syria_time()
    current = now.strftime("%H:%M")
    return opening <= current <= closing


def is_closed_day(closed_days_str: str) -> bool:
    """Check if today is a closed day."""
    now = get_syria_time()
    current_day = DAYS_EN[now.weekday()]
    closed = [d.strip().lower() for d in closed_days_str.split(",") if d.strip()]
    return current_day in closed


def get_away_message(merchant_name: str, opening: str, closing: str, closed_days: str) -> str:
    """Generate an away message for when the business is closed."""
    now = get_syria_time()
    current_day_ar = DAYS_AR[now.weekday()]

    if is_closed_day(closed_days):
        return (
            f"عذراً، {merchant_name} مسكر اليوم ({current_day_ar}).\n"
            f"ساعات العمل: {opening} - {closing}\n"
            f"رح نرد عليك أول ما نفتح! 🙏"
        )

    return (
        f"عذراً، {merchant_name} مسكر حالياً.\n"
        f"ساعات العمل: {opening} - {closing}\n"
        f"ابعتلنا رسالة ورح نرد عليك أول ما نفتح! 📩"
    )


def get_next_opening(opening: str, closed_days_str: str) -> str:
    """Get the next opening time as a human-readable string."""
    from datetime import timedelta

    now = get_syria_time()
    closed = [d.strip().lower() for d in closed_days_str.split(",") if d.strip()]

    # Check next 7 days
    for i in range(1, 8):
        future = now + timedelta(days=i)
        day_en = DAYS_EN[future.weekday()]
        day_ar = DAYS_AR[future.weekday()]

        if day_en not in closed:
            if i == 1:
                return f"بكرا الساعة {opening}"
            else:
                return f"يوم {day_ar} الساعة {opening}"

    return f"الساعة {opening}"
