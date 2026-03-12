"""
Pytest configuration and fixtures for the real estate prediction API tests.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from src.app.main import app
from src.inference.model import get_model
from pathlib import Path
import pandas as pd
import numpy as np


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="session")
def mock_model():
    """Create a mock model that returns predictable predictions."""
    mock_pipeline = Mock()
    
    def mock_predict(df):
        # Return a predictable value based on surface_habitable
        surface = df['Surface habitable'].iloc[0]
        return np.array([np.log(surface * 5000)])  # ~5000€/m²
    
    mock_pipeline.predict = mock_predict
    return mock_pipeline


@pytest.fixture(scope="session")
def mock_geocoding_success():
    """Mock successful geocoding response."""
    return {
        'address': '1 Boulevard Victor Hugo, 75016 Paris',
        'latitude': 48.866667,
        'longitude': 2.266667,
        'postcode': '75016',
        'city': 'Paris',
        'citycode': '75116',
        'type': 'housenumber',
        'score': 0.9
    }


@pytest.fixture(scope="session")
def mock_geocoding_failure():
    """Mock failed geocoding response."""
    return {
        'address': '',
        'latitude': 0.0,
        'longitude': 0.0,
        'postcode': '',
        'city': '',
        'citycode': '',
        'type': '',
        'score': 0.1
    }


@pytest.fixture(autouse=True)
def mock_geocoding_api():
    """Automatically mock the geocoding API to avoid external calls during tests."""
    with patch('src.utils.geo.requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def valid_prediction_input():
    """Return valid input data for prediction tests."""
    return {
        'type_local': 'Appartement',
        'address': '1 Boulevard Victor Hugo, Paris',
        'surface_habitable': 80.0,
        'nombre_pieces': 3,
        'surface_terrain': 100.0
    }


@pytest.fixture
def invalid_prediction_input():
    """Return invalid input data for prediction tests."""
    return {
        'type_local': 'Appartement',
        'address': 'Invalid Address 123',
        'surface_habitable': 80.0,
        'nombre_pieces': 3,
        'surface_terrain': 100.0
    }
