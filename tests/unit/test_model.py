"""
Unit tests for the model inference functionality.
"""
import pytest
from unittest.mock import patch, Mock
from src.inference.model import get_estimation, AddressNotFoundError, normalize_street_type
import pandas as pd
import numpy as np


class TestNormalizeStreetType:
    """Test the street type normalization function."""
    
    def test_common_street_types(self):
        """Test normalization of common French street types."""
        assert normalize_street_type("rue") == "RUE"
        assert normalize_street_type("Rue") == "RUE"
        assert normalize_street_type("RUE") == "RUE"
        assert normalize_street_type("avenue") == "AV"
        assert normalize_street_type("boulevard") == "BD"
        assert normalize_street_type("allée") == "ALL"
        assert normalize_street_type("allee") == "ALL"
        assert normalize_street_type("chemin") == "CHE"
        assert normalize_street_type("impasse") == "IMP"
        assert normalize_street_type("place") == "PL"
        assert normalize_street_type("résidence") == "RES"
        assert normalize_street_type("residence") == "RES"
        assert normalize_street_type("route") == "RTE"
    
    def test_unknown_street_type(self):
        """Test unknown street types return NAN."""
        assert normalize_street_type("unknown") == "NAN"
        assert normalize_street_type("") == "NAN"
        assert normalize_street_type("123") == "NAN"


class TestGetEstimation:
    """Test the get_estimation function."""
    
    @patch('src.inference.model.validate_and_geocode_address')
    @patch('src.inference.model.model_predict')
    def test_successful_estimation(self, mock_predict, mock_geocode):
        """Test successful estimation with valid address."""
        # Setup mocks
        mock_geocode.return_value = (True, {
            'address': '1 Boulevard Victor Hugo, 75016 Paris',
            'latitude': 48.866667,
            'longitude': 2.266667,
            'citycode': '75116',
            'type': 'housenumber',
            'score': 0.9
        })
        
        mock_predict.return_value = 400000.0
        
        # Mock model
        mock_model = Mock()
        
        # Call function
        result = get_estimation(
            model=mock_model,
            address='1 Boulevard Victor Hugo, Paris',
            type_local='Appartement',
            surface_habitable=80.0,
            surface_terrain=100.0,
            nombre_pieces=3
        )
        
        # Assertions
        assert result['input']['type'] == 'Appartement'
        assert result['input']['address'] == '1 Boulevard Victor Hugo, 75016 Paris'
        assert result['input']['surface_habitable'] == 80.0
        assert result['input']['nombre_pieces'] == 3
        assert result['input']['surface_terrain'] == 100.0
        
        assert result['coordinates']['latitude'] == 48.866667
        assert result['coordinates']['longitude'] == 2.266667
        assert result['coordinates']['commune'] == '75116'
        
        assert result['estimation']['price'] == 400000.0
        assert result['estimation']['price_per_m2'] == 5000
        assert result['estimation']['confidence_interval']['min'] == 380000
        assert result['estimation']['confidence_interval']['max'] == 420000
        assert result['estimation']['confidence_level'] == 'high'
        
        assert result['metadata']['address_score'] == 0.9
        assert result['metadata']['address_type'] == 'housenumber'
    
    @patch('src.inference.model.validate_and_geocode_address')
    def test_invalid_address_raises_error(self, mock_geocode):
        """Test that invalid address raises AddressNotFoundError."""
        mock_geocode.return_value = (False, None)
        
        mock_model = Mock()
        
        with pytest.raises(AddressNotFoundError) as exc_info:
            get_estimation(
                model=mock_model,
                address='Invalid Address',
                type_local='Appartement',
                surface_habitable=80.0,
                surface_terrain=100.0,
                nombre_pieces=3
            )
        
        assert "Adresse introuvable" in str(exc_info.value)
    
    @patch('src.inference.model.validate_and_geocode_address')
    @patch('src.inference.model.model_predict')
    def test_medium_confidence_level(self, mock_predict, mock_geocode):
        """Test confidence level is medium for non-housenumber addresses."""
        mock_geocode.return_value = (True, {
            'address': 'Boulevard Victor Hugo, 75016 Paris',
            'latitude': 48.866667,
            'longitude': 2.266667,
            'citycode': '75116',
            'type': 'street',  # Not housenumber
            'score': 0.7
        })
        
        mock_predict.return_value = 400000.0
        mock_model = Mock()
        
        result = get_estimation(
            model=mock_model,
            address='Boulevard Victor Hugo, Paris',
            type_local='Appartement',
            surface_habitable=80.0,
            surface_terrain=100.0,
            nombre_pieces=3
        )
        
        assert result['estimation']['confidence_level'] == 'medium'


class TestModelPredict:
    """Test the model_predict function."""
    
    @patch('src.inference.model.pd.DataFrame')
    def test_model_predict_calls_predict(self, mock_dataframe):
        """Test that model_predict calls the model's predict method correctly."""
        # Setup mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([10.0])
        
        # Setup mock DataFrame
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        # Mock input data
        model_input = {
            'Type local': ['Appartement'],
            'latitude': [48.866667],
            'longitude': [2.266667],
            'Surface habitable': [80.0],
            'Nombre pieces principales': [3],
            'Surface terrain': [100.0],
            'Type de voie': ['BD'],
            'densite': [1200]
        }
        
        # Call function
        from src.inference.model import model_predict
        result = model_predict(mock_model, model_input)
        
        # Assertions
        mock_model.predict.assert_called_once_with(mock_df)
        assert result == np.exp(10.0)
