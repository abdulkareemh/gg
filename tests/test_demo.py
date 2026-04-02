"""Tests for demo chat simulator."""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestDemoChat:
    def test_greeting(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test1", "message": "مرحبا"})
        assert resp.status_code == 200
        data = resp.json()
        assert "أهلا" in data["reply"]
        assert data["action"] == "greeting"

    def test_show_menu(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test2", "message": "القائمة"})
        assert resp.status_code == 200
        data = resp.json()
        assert "شاورما" in data["reply"]

    def test_order_product(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test3", "message": "بدي شاورما"})
        assert resp.status_code == 200
        data = resp.json()
        assert "شاورما" in data["reply"]
        assert "سلّتك" in data["reply"]

    def test_order_with_quantity(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test4", "message": "2 فلافل"})
        data = resp.json()
        assert "فلافل" in data["reply"]
        assert "30,000" in data["reply"]  # 2 * 15000

    def test_confirm_order(self):
        # Add item
        client.post("/api/demo/chat", json={"session_id": "test5", "message": "شاورما"})
        # Confirm
        resp = client.post("/api/demo/chat", json={"session_id": "test5", "message": "تأكيد"})
        data = resp.json()
        assert "تم تأكيد" in data["reply"]
        assert data["action"] == "order_confirmed"

    def test_cancel_order(self):
        client.post("/api/demo/chat", json={"session_id": "test6", "message": "فلافل"})
        resp = client.post("/api/demo/chat", json={"session_id": "test6", "message": "الغي"})
        data = resp.json()
        assert "إلغاء" in data["reply"]

    def test_help(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test7", "message": "مساعدة"})
        data = resp.json()
        assert "help" == data["action"] or "auto_reply" == data["action"]

    def test_faq_hours(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test8", "message": "ساعات العمل"})
        data = resp.json()
        assert "09:00" in data["reply"]

    def test_faq_payment(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test9", "message": "كيف بدفع"})
        data = resp.json()
        assert "كاش" in data["reply"]

    def test_unknown_message(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test10", "message": "xyz123random"})
        data = resp.json()
        assert data["action"] == "unknown"

    def test_multiple_items_cart(self):
        sid = "test11"
        client.post("/api/demo/chat", json={"session_id": sid, "message": "شاورما"})
        resp = client.post("/api/demo/chat", json={"session_id": sid, "message": "عصير"})
        data = resp.json()
        # Cart should have both items
        assert "شاورما" in data["reply"]
        assert "عصير" in data["reply"]

    def test_check_order_no_history(self):
        resp = client.post("/api/demo/chat", json={"session_id": "test12", "message": "وين طلبيتي"})
        data = resp.json()
        assert "ما لقيت" in data["reply"]

    def test_check_order_after_placing(self):
        sid = "test13"
        client.post("/api/demo/chat", json={"session_id": sid, "message": "فلافل"})
        client.post("/api/demo/chat", json={"session_id": sid, "message": "تأكيد"})
        resp = client.post("/api/demo/chat", json={"session_id": sid, "message": "وين طلبيتي"})
        data = resp.json()
        assert "قيد التحضير" in data["reply"]


class TestDemoEndpoints:
    def test_products(self):
        resp = client.get("/api/demo/products")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["products"]) == 10

    def test_info(self):
        resp = client.get("/api/demo/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["merchant"]["business_name"] == "مطعم أبو خالد"

    def test_reset(self):
        # Create session
        client.post("/api/demo/chat", json={"session_id": "reset_test", "message": "شاورما"})
        # Reset
        resp = client.post("/api/demo/reset?session_id=reset_test")
        assert resp.status_code == 200
        assert resp.json()["status"] == "reset"

    def test_demo_page(self):
        resp = client.get("/demo")
        assert resp.status_code == 200
