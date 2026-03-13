"""
Integration tests for the FastAPI endpoints.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
import json


class TestHomeEndpoint:
    """Test the home endpoint."""

    def test_home_returns_html(self, test_client):
        """Test that home endpoint returns HTML response."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<html" in response.text


class TestHealthCheckEndpoint:
    """Test the health check endpoint."""

    def test_healthcheck_returns_ok(self, test_client):
        """Test that health check endpoint returns OK status."""
        response = test_client.get("/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


class TestPredictionEndpoint:
    """Test the prediction endpoint."""

    @patch("src.app.routes.get_estimation")
    def test_predict_success(self, mock_get_estimation, test_client):
        """Test successful prediction with valid input."""
        mock_get_estimation.return_value = {
            "input": {
                "type": "Appartement",
                "address": "1 Boulevard Victor Hugo, 75016 Paris",
                "surface_habitable": 80.0,
                "nombre_pieces": 3,
                "surface_terrain": 100.0,
            },
            "coordinates": {
                "latitude": 48.866667,
                "longitude": 2.266667,
                "commune": "75116",
            },
            "estimation": {
                "price": 400000.0,
                "price_per_m2": 5000,
                "confidence_interval": {"min": 380000, "max": 420000},
                "confidence_level": "high",
            },
            "metadata": {"address_score": 0.9, "address_type": "housenumber"},
        }

        response = test_client.post(
            "/predict",
            data={
                "type_local": "Appartement",
                "address": "1 Boulevard Victor Hugo, Paris",
                "surface_habitable": 80.0,
                "nombre_pieces": 3,
                "surface_terrain": 100.0,
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        mock_get_estimation.assert_called_once()

    @patch("src.app.routes.get_estimation")
    def test_predict_address_not_found(self, mock_get_estimation, test_client):
        """Test prediction with invalid address raises AddressNotFoundError."""
        from src.inference.model import AddressNotFoundError

        mock_get_estimation.side_effect = AddressNotFoundError("Adresse introuvable")

        response = test_client.post(
            "/predict",
            data={
                "type_local": "Appartement",
                "address": "Invalid Address 123",
                "surface_habitable": 80.0,
                "nombre_pieces": 3,
                "surface_terrain": 100.0,
            },
        )

        assert response.status_code == 500
        assert "Adresse introuvable" in response.text

    def test_predict_missing_required_fields(self, test_client):
        """Test prediction with missing required fields."""
        response = test_client.post(
            "/predict",
            data={
                "type_local": "Appartement",
                "address": "1 Boulevard Victor Hugo, Paris",
            },
        )

        assert response.status_code == 422


class TestChatbotEndpoint:
    """Test the chatbot endpoint."""

    def test_chatbot_returns_html(self, test_client):
        """Test that chatbot endpoint returns HTML response."""
        response = test_client.get("/chatbot")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<html" in response.text


class TestChatEndpoint:
    """Test the chat endpoint."""

    @patch("src.app.routes.agent_immo")
    def test_chat_success(self, mock_agent, test_client):
        """Test successful chat response."""
        mock_message = Mock()
        mock_message.content = "Bonjour, comment puis-je vous aider ?"

        mock_agent.ainvoke = AsyncMock(
            return_value={"messages": [mock_message]}
        )

        response = test_client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "Bonjour, comment puis-je vous aider ?"
        }

    def test_chat_missing_messages(self, test_client):
        """Test chat with missing messages field."""
        response = test_client.post("/chat", json={})
        assert response.status_code == 422

    def test_chat_invalid_message_format(self, test_client):
        """Test chat with invalid message format."""
        response = test_client.post(
            "/chat",
            json={"messages": [{"invalid": "format"}]},
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    """Test the streaming chat endpoint."""

    @patch("src.app.routes.agent_immo")
    def test_stream_returns_event_stream(self, mock_agent, test_client):
        """Test that stream endpoint returns SSE content type."""
        async def fake_events(*args, **kwargs):
            chunk = Mock()
            chunk.content = "Bonjour"
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": chunk},
            }

        mock_agent.astream_events = fake_events

        response = test_client.post(
            "/chat/stream",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "Bonjour" in response.text

    def test_stream_missing_messages(self, test_client):
        """Test stream with missing messages field."""
        response = test_client.post("/chat/stream", json={})
        assert response.status_code == 422