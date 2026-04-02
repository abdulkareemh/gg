"""Analytics agent — provides business insights via chat.

Merchants can ask questions like:
- "كم بعنا اليوم؟"
- "شو الأكثر طلباً؟"
- "كيف المبيعات هالأسبوع؟"
"""

from src.agents.base_agent import BaseAgent, AgentResponse
from src.services.report_service import format_daily_report, format_weekly_report


class AnalyticsAgent(BaseAgent):
    """Provides business analytics and insights via chat."""

    async def handle(self, merchant_id: int, message: str, context: dict) -> AgentResponse:
        intent = context.get("intent", "report")

        # Use Claude to understand the analytics question
        response_text = await self.ask_claude(
            ANALYTICS_PROMPT,
            f"Merchant asks: {message}\n"
            f"Available data context: {context.get('analytics_data', 'No data loaded')}",
        )

        return AgentResponse(
            text=response_text,
            text_ar=response_text,
            action="analytics_response",
            data={"query": message},
        )


ANALYTICS_PROMPT = """أنت نور، مساعد تحليلات ذكي لأصحاب المحلات في سوريا.
أجب عن أسئلة التاجر حول المبيعات والأداء باللهجة السورية.
كن مختصراً واستخدم الأرقام والإحصائيات.
إذا ما عندك بيانات كافية، قل ذلك بأدب.

أمثلة على الأجوبة:
- "اليوم بعنا 23 طلبية بمجموع 575,000 ل.س 📈"
- "الأكثر طلباً: شاورما دجاج (45 حبة) 🏆"
- "مبيعات هالأسبوع أحسن من الأسبوع اللي قبل بـ 15% 📊"
"""
