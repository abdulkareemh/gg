"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "noor-ai"


class TestWhatsAppWebhook:
    def test_verify_valid_token(self):
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub_mode": "subscribe",
                "hub_verify_token": "",  # matches default empty config
                "hub_challenge": "12345",
            },
        )
        assert response.status_code == 200

    def test_verify_invalid_token(self):
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub_mode": "subscribe",
                "hub_verify_token": "wrong-token",
                "hub_challenge": "12345",
            },
        )
        assert response.status_code == 403
