"""Central message handler — the brain that ties everything together.

This is the main pipeline:
  Message In → Session → NLP → Agent → DB → Response → Message Out
"""

from src.agents.router import AgentRouter
from src.integrations.whatsapp import WhatsAppClient
from src.integrations.telegram import TelegramClient
from src.services.session_service import SessionService
from src.nlp.syrian_arabic import detect_intent, is_arabic


class MessageHandler:
    """Processes incoming messages end-to-end."""

    def __init__(self):
        self.agent_router = AgentRouter()
        self.session_service = SessionService()
        self.whatsapp = WhatsAppClient()
        self.telegram = TelegramClient()

    async def handle_message(self, phone: str, text: str, platform: str) -> str:
        """Process an incoming message and send a response.

        Returns the response text that was sent.
        """
        # 1. Load or create session
        session = await self.session_service.add_to_history(phone, "user", text)

        # 2. Check if we're in a multi-step flow
        if session["state"] == "onboarding":
            return await self._handle_onboarding(phone, text, session, platform)

        if session["state"] == "ordering":
            return await self._handle_ordering_flow(phone, text, session, platform)

        # 3. Detect intent and route to agent
        intent, confidence = detect_intent(text)

        # 4. Build context from session + DB
        context = {
            "phone": phone,
            "platform": platform,
            "intent": intent,
            "confidence": confidence,
            "session": session,
            "cart": session.get("cart", []),
        }

        # 5. Route to the right agent
        merchant_id = session.get("merchant_id", 0)
        response = await self.agent_router.route(merchant_id, text, context)

        # 6. Save bot response to history
        await self.session_service.add_to_history(phone, "bot", response.text_ar)

        # 7. Send response back to user
        reply = response.text_ar
        await self._send_reply(phone, reply, platform)

        return reply

    async def _handle_onboarding(self, phone: str, text: str, session: dict, platform: str) -> str:
        """Handle merchant self-registration flow."""
        step = session.get("step")

        if step == "ask_name":
            session["temp_data"]["name"] = text
            session["step"] = "ask_business"
            await self.session_service.save_session(phone, session)
            reply = "تمام! شو اسم المحل أو البزنس تبعك؟"

        elif step == "ask_business":
            session["temp_data"]["business_name"] = text
            session["step"] = "ask_type"
            await self.session_service.save_session(phone, session)
            reply = "حلو! شو نوع البزنس؟\n1. مطعم 🍽️\n2. محل 🏪\n3. خدمات 🔧\n4. غير ذلك"

        elif step == "ask_type":
            type_map = {"1": "restaurant", "2": "shop", "3": "service", "4": "other"}
            business_type = type_map.get(text.strip(), text)
            session["temp_data"]["business_type"] = business_type
            session["step"] = "ask_city"
            await self.session_service.save_session(phone, session)
            reply = "وين موقعك؟ (مثلاً: دمشق، حلب، حمص...)"

        elif step == "ask_city":
            session["temp_data"]["city"] = text
            # Registration complete
            data = session["temp_data"]
            session["state"] = "idle"
            session["step"] = None
            session["temp_data"] = {}
            await self.session_service.save_session(phone, session)
            reply = (
                f"تمام يا {data['name']}! تم تسجيل {data['business_name']} بنجاح ✅\n\n"
                f"هلق بقدر ساعدك بـ:\n"
                f"• إدارة الطلبيات\n"
                f"• متابعة الزبائن\n"
                f"• إدارة المخزون\n\n"
                f"ابعتلي 'مساعدة' إذا بدك تعرف أكتر!"
            )
        else:
            # Start onboarding
            session["state"] = "onboarding"
            session["step"] = "ask_name"
            await self.session_service.save_session(phone, session)
            reply = "أهلا وسهلا بنور! 🌟\nأنا مساعدك الذكي للبزنس.\nشو اسمك الكريم؟"

        await self.session_service.add_to_history(phone, "bot", reply)
        await self._send_reply(phone, reply, platform)
        return reply

    async def _handle_ordering_flow(self, phone: str, text: str, session: dict, platform: str) -> str:
        """Handle multi-step ordering conversation."""
        step = session.get("step")
        cart = session.get("cart", [])

        if step == "confirm_order":
            if any(w in text.lower() for w in ["نعم", "اي", "تمام", "اكيد", "yes", "ok"]):
                # Confirm the order
                total = sum(item["total"] for item in cart)
                session["state"] = "idle"
                session["step"] = None
                await self.session_service.clear_cart(phone)
                await self.session_service.save_session(phone, session)
                reply = (
                    f"تم تأكيد طلبيتك! ✅\n"
                    f"المجموع: {total:,.0f} ل.س\n"
                    f"رح نبعتلك تحديث لما تصير جاهزة. شكراً! 🙏"
                )
            else:
                session["state"] = "idle"
                session["step"] = None
                await self.session_service.clear_cart(phone)
                await self.session_service.save_session(phone, session)
                reply = "تم إلغاء الطلبية. إذا بدك تطلب شي تاني، ابعتلي!"
        else:
            session["state"] = "idle"
            await self.session_service.save_session(phone, session)
            reply = "شو بدك تطلب؟ ابعتلي 'القائمة' لأعرضلك المنتجات."

        await self.session_service.add_to_history(phone, "bot", reply)
        await self._send_reply(phone, reply, platform)
        return reply

    async def _send_reply(self, phone: str, text: str, platform: str) -> None:
        """Send a reply back to the user on their platform."""
        try:
            if platform == "whatsapp":
                await self.whatsapp.send_text(phone, text)
            elif platform == "telegram":
                await self.telegram.send_text(phone, text)
        except Exception as e:
            # Log error but don't crash — message is still saved in session
            print(f"[ERROR] Failed to send message to {phone} via {platform}: {e}")
