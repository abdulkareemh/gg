"""Interactive merchant onboarding guide.

Guides new merchants step-by-step through setting up their
Noor AI bot after registration.
"""


ONBOARDING_STEPS = [
    {
        "id": "welcome",
        "message": (
            "أهلا فيك بنور! 🌟\n\n"
            "رح ساعدك تجهّز البوت تبعك بـ 5 خطوات بسيطة.\n"
            "كل خطوة بتاخد أقل من دقيقة.\n\n"
            "جاهز؟ ابعت 'يلا' لنبدأ! 🚀"
        ),
    },
    {
        "id": "add_products",
        "message": (
            "📋 الخطوة 1: أضف منتجاتك\n\n"
            "ابعتلي قائمة منتجاتك بهالشكل:\n"
            "اسم المنتج — السعر\n\n"
            "مثلاً:\n"
            "شاورما دجاج — 25000\n"
            "فلافل — 15000\n"
            "عصير برتقال — 5000\n\n"
            "أو ابعتلي ملف CSV إذا عندك قائمة جاهزة.\n"
            "ابعت 'تم' لما تخلص."
        ),
    },
    {
        "id": "set_hours",
        "message": (
            "🕐 الخطوة 2: ساعات العمل\n\n"
            "شو ساعات عملك؟\n"
            "مثلاً: 9:00 - 23:00\n\n"
            "وشو الأيام المسكّرة؟\n"
            "مثلاً: الجمعة"
        ),
    },
    {
        "id": "delivery_zones",
        "message": (
            "🚚 الخطوة 3: مناطق التوصيل\n\n"
            "وين بتوصّلو؟ ابعتلي المناطق مع رسوم التوصيل:\n"
            "المنطقة — رسوم التوصيل\n\n"
            "مثلاً:\n"
            "المزة — 10000\n"
            "باب توما — 8000\n\n"
            "ابعت 'ما بوصّل' إذا ما عندك توصيل.\n"
            "ابعت 'تم' لما تخلص."
        ),
    },
    {
        "id": "test_order",
        "message": (
            "🧪 الخطوة 4: طلبية تجريبية\n\n"
            "جرّب تبعت طلبية تجريبية كأنك زبون:\n"
            "ابعت 'بدي اطلب' وجرّب التجربة كاملة.\n\n"
            "هيك بتتأكد إنو كلشي شغّال تمام!"
        ),
    },
    {
        "id": "share",
        "message": (
            "📢 الخطوة 5: شارك البوت مع زبائنك!\n\n"
            "كلشي جاهز! هلق شارك رقم الواتساب مع زبائنك:\n"
            "• حطّو بالبايو تبع الإنستغرام\n"
            "• ابعتو لزبائنك عالواتساب\n"
            "• اطبعو على كرتون المحل\n\n"
            "رح ابعتلك رابط المشاركة الجاهز..."
        ),
    },
    {
        "id": "complete",
        "message": (
            "🎉 تمام! محلك جاهز على نور!\n\n"
            "ملخص:\n"
            "✅ المنتجات مضافة\n"
            "✅ ساعات العمل محددة\n"
            "✅ مناطق التوصيل مجهزة\n"
            "✅ الطلبية التجريبية نجحت\n\n"
            "هلق نور رح يستقبل الطلبيات بالنيابة عنك 24/7!\n"
            "ابعت 'مساعدة' بأي وقت إذا بدك شي. بالتوفيق! 💪"
        ),
    },
]


class OnboardingGuide:
    """Manages the step-by-step onboarding flow."""

    def get_step(self, step_index: int) -> dict | None:
        """Get an onboarding step by index."""
        if 0 <= step_index < len(ONBOARDING_STEPS):
            return ONBOARDING_STEPS[step_index]
        return None

    def get_step_count(self) -> int:
        return len(ONBOARDING_STEPS)

    def get_progress(self, current_step: int) -> str:
        """Get a progress bar string."""
        total = len(ONBOARDING_STEPS) - 2  # Exclude welcome and complete
        completed = min(max(current_step - 1, 0), total)
        bar = "●" * completed + "○" * (total - completed)
        return f"[{bar}] {completed}/{total}"

    def get_step_message(self, step_index: int) -> str:
        """Get the message for a step with progress indicator."""
        step = self.get_step(step_index)
        if not step:
            return ONBOARDING_STEPS[-1]["message"]  # Complete message

        if step["id"] not in ("welcome", "complete"):
            progress = self.get_progress(step_index)
            return f"{progress}\n\n{step['message']}"

        return step["message"]
