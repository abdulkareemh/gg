"""Customer feedback collection agent.

Automatically asks for feedback after order completion
and processes the responses into actionable insights.
"""

from src.agents.base_agent import BaseAgent, AgentResponse
from src.nlp.syrian_arabic import detect_intent, normalize_arabic


# Sentiment keywords for quick analysis
POSITIVE_WORDS = [
    "ممتاز", "رائع", "حلو", "زاكي", "طيب", "عظيم", "تمام",
    "أحسن", "يسلمو", "شكراً", "great", "amazing", "good", "perfect",
]

NEGATIVE_WORDS = [
    "سيء", "بارد", "متأخر", "غلط", "خطأ", "مش منيح", "ناقص",
    "بطيء", "غالي", "bad", "late", "wrong", "terrible", "cold",
]

FEEDBACK_QUESTIONS = {
    "overall": "كيف كانت تجربتك معنا؟ قيّمنا من 1 لـ 5 ⭐",
    "food_quality": "كيف كان الأكل؟ (ممتاز / جيد / عادي / سيء)",
    "delivery_speed": "كيف كانت سرعة التوصيل؟",
    "suggestion": "عندك أي اقتراح لتحسين خدمتنا؟",
}


class FeedbackAgent(BaseAgent):
    """Collects and analyzes customer feedback after orders."""

    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        step = context.get("feedback_step")

        if step is None:
            return self._ask_rating()
        elif step == "rating":
            return self._process_rating(message, context)
        elif step == "comment":
            return self._process_comment(message, context)
        else:
            return self._thank_customer(context)

    def _ask_rating(self) -> AgentResponse:
        return AgentResponse(
            text="Asking for rating",
            text_ar=(
                "شكراً إنك طلبت منّا! 🙏\n\n"
                "كيف كانت تجربتك؟ قيّمنا من 1 لـ 5:\n"
                "1️⃣ سيء\n"
                "2️⃣ عادي\n"
                "3️⃣ جيد\n"
                "4️⃣ كتير منيح\n"
                "5️⃣ ممتاز!"
            ),
            action="ask_rating",
            data={"feedback_step": "rating"},
        )

    def _process_rating(self, message: str, context: dict) -> AgentResponse:
        # Extract rating number
        rating = None
        for char in message:
            if char.isdigit() and 1 <= int(char) <= 5:
                rating = int(char)
                break

        if rating is None:
            # Try sentiment analysis
            normalized = normalize_arabic(message.lower())
            if any(w in normalized for w in POSITIVE_WORDS):
                rating = 5
            elif any(w in normalized for w in NEGATIVE_WORDS):
                rating = 2
            else:
                return AgentResponse(
                    text="Could not parse rating",
                    text_ar="ممكن تقيّمنا برقم من 1 لـ 5؟ ⭐",
                    action="ask_rating_retry",
                    data={"feedback_step": "rating"},
                )

        if rating >= 4:
            text_ar = f"شكراً! {rating}⭐ — منبسطين إنك مبسوط! 😊\nبدك تضيف تعليق أو اقتراح؟ (ابعت 'لا' للتخطي)"
        elif rating == 3:
            text_ar = f"{rating}⭐ — شكراً لصراحتك. شو بنقدر نحسّن؟"
        else:
            text_ar = f"{rating}⭐ — نعتذر عن التجربة. شو كانت المشكلة عشان نحسّن؟"

        return AgentResponse(
            text=f"Rating: {rating}",
            text_ar=text_ar,
            action="rating_received",
            data={"feedback_step": "comment", "rating": rating},
        )

    def _process_comment(self, message: str, context: dict) -> AgentResponse:
        skip_words = ["لا", "لأ", "no", "skip", "تخطي"]
        if message.strip().lower() in skip_words:
            return self._thank_customer(context)

        sentiment = self._analyze_sentiment(message)

        return AgentResponse(
            text=f"Comment received. Sentiment: {sentiment}",
            text_ar="شكراً كتير على ملاحظاتك! رح ناخدها بعين الاعتبار 💪",
            action="feedback_complete",
            data={
                "feedback_step": "done",
                "comment": message,
                "sentiment": sentiment,
            },
        )

    def _thank_customer(self, context: dict) -> AgentResponse:
        return AgentResponse(
            text="Feedback complete",
            text_ar="شكراً إلك! منتمنى نشوفك عنّا كمان مرة 🌟",
            action="feedback_done",
            data={"feedback_step": "done"},
        )

    def _analyze_sentiment(self, text: str) -> str:
        """Quick sentiment analysis on feedback text."""
        normalized = normalize_arabic(text.lower())
        pos_count = sum(1 for w in POSITIVE_WORDS if w in normalized)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in normalized)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"
