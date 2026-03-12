"""
Integration tests for the FastAPI endpoints.
"""
import pytest
from unittest.mock import patch, Mock
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
        assert response.json() == {'status': 'OK'}


class TestPredictionEndpoint:
    """Test the prediction endpoint."""
    
    @patch('src.app.routes.get_model')
    @patch('src.app.routes.validate_and_geocode_address')
    @patch('src.app.routes.get_estimation')
    def test_predict_success(self, mock_get_estimation, mock_geocode, mock_get_model, test_client):
        """Test successful prediction with valid input."""
        # Setup mocks
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        
        mock_geocode.return_value = (True, {
            'address': '1 Boulevard Victor Hugo, 75016 Paris',
            'latitude': 48.866667,
            'longitude': 2.266667,
            'citycode': '75116',
            'type': 'housenumber',
            'score': 0.9
        })
        
        mock_get_estimation.return_value = {
            'input': {
                'type': 'Appartement',
                'address': '1 Boulevard Victor Hugo, 75016 Paris',
                'surface_habitable': 80.0,
                'nombre_pieces': 3,
                'surface_terrain': 100.0
            },
            'coordinates': {
                'latitude': 48.866667,
                'longitude': 2.266667,
                'commune': '75116'
            },
            'estimation': {
                'price': 400000.0,
                'price_per_m2': 5000,
                'confidence_interval': {'min': 380000, 'max': 420000},
                'confidence_level': 'high'
            },
            'metadata': {
                'address_score': 0.9,
                'address_type': 'housenumber'
            }
        }
        
        # Make request
        response = test_client.post("/predict", data={
            'type_local': 'Appartement',
            'address': '1 Boulevard Victor Hugo, Paris',
            'surface_habitable': 80.0,
            'nombre_pieces': 3,
            'surface_terrain': 100.0
        })
        
        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "400 000" in response.text
        assert "5 000" in response.text
    
    @patch('src.app.routes.get_model')
    @patch('src.app.routes.validate_and_geocode_address')
    def test_predict_invalid_address(self, mock_geocode, mock_get_model, test_client):
        """Test prediction with invalid address."""
        # Setup mocks
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        mock_geocode.return_value = (False, None)
        
        # Make request
        response = test_client.post("/predict", data={
            'type_local': 'Appartement',
            'address': 'Invalid Address 123',
            'surface_habitable': 80.0,
            'nombre_pieces': 3,
            'surface_terrain': 100.0
        })
        
        # Should return error response
        assert response.status_code == 500
        assert "Adresse introuvable" in response.text
        assert "Erreur" in response.text
    
    def test_predict_missing_required_fields(self, test_client):
        """Test prediction with missing required fields."""
        response = test_client.post("/predict", data={
            'type_local': 'Appartement',
            'address': '1 Boulevard Victor Hugo, Paris',
            # Missing surface_habitable and nombre_pieces
        })
        
        assert response.status_code == 422  # Unprocessable Entity


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
    
    @patch('src.app.routes.agent_immo.ainvoke')
    async def test_chat_success(self, mock_ainvoke, test_client):
        """Test successful chat response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.get.return_value = [
            Mock(role="assistant", content="Hello, how can I help you?")
        ]
        mock_ainvoke.return_value = mock_response
        
        # Make request
        response = test_client.post("/chat", json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        })
        
        # Assertions
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, how can I help you?"}
    
    def test_chat_missing_messages(self, test_client):
        """Test chat with missing messages field."""
        response = test_client.post("/chat", json={})
        assert response.status_code == 422  # Unprocessable Entity
