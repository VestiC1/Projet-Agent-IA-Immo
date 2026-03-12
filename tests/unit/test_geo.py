"""
Unit tests for the geocoding utility functions.
"""
import pytest
from unittest.mock import patch, Mock
from src.utils.geo import validate_and_geocode_address
import requests


class TestValidateAndGeocodeAddress:
    """Test the validate_and_geocode_address function."""
    
    def test_empty_address(self):
        """Test empty address returns False."""
        is_valid, result = validate_and_geocode_address("")
        assert is_valid is False
        assert result is None
    
    def test_short_address(self):
        """Test short address returns False."""
        is_valid, result = validate_and_geocode_address("abc")
        assert is_valid is False
        assert result is None
    
    @patch('src.utils.geo.requests.get')
    def test_successful_geocoding(self, mock_get):
        """Test successful geocoding with valid API response."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [2.266667, 48.866667]
                    },
                    "properties": {
                        "label": "1 Boulevard Victor Hugo 75016 Paris",
                        "score": 0.9,
                        "postcode": "75016",
                        "city": "Paris",
                        "citycode": "75116",
                        "type": "housenumber"
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call function
        is_valid, result = validate_and_geocode_address("1 Boulevard Victor Hugo, Paris")
        
        # Assertions
        assert is_valid is True
        assert result['address'] == "1 Boulevard Victor Hugo 75016 Paris"
        assert result['latitude'] == 48.866667
        assert result['longitude'] == 2.266667
        assert result['postcode'] == "75016"
        assert result['city'] == "Paris"
        assert result['citycode'] == "75116"
        assert result['type'] == "housenumber"
        assert result['score'] == 0.9
    
    @patch('src.utils.geo.requests.get')
    def test_failed_geocoding_no_features(self, mock_get):
        """Test failed geocoding when API returns no features."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": []
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call function
        is_valid, result = validate_and_geocode_address("Invalid Address")
        
        # Assertions
        assert is_valid is False
        assert result is None
    
    @patch('src.utils.geo.requests.get')
    def test_low_score_address(self, mock_get):
        """Test address with low score returns False."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [2.266667, 48.866667]
                    },
                    "properties": {
                        "label": "Some Address",
                        "score": 0.4,  # Low score
                        "postcode": "75016",
                        "city": "Paris",
                        "citycode": "75116",
                        "type": "street"
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call function
        is_valid, result = validate_and_geocode_address("Some Address")
        
        # Assertions
        assert is_valid is False
        assert result is not None  # Result is returned but not valid
        assert result['score'] == 0.4
    
    @patch('src.utils.geo.requests.get')
    def test_api_error(self, mock_get):
        """Test API error handling."""
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        # Call function
        is_valid, result = validate_and_geocode_address("Some Address")
        
        # Assertions
        assert is_valid is False
        assert result is None
    
    @patch('src.utils.geo.requests.get')
    def test_http_error(self, mock_get):
        """Test HTTP error handling."""
        # Setup mock to raise HTTPError
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        # Call function
        is_valid, result = validate_and_geocode_address("Some Address")
        
        # Assertions
        assert is_valid is False
        assert result is None
    
    def test_api_url_and_params(self):
        """Test that the correct API URL and parameters are used."""
        with patch('src.utils.geo.requests.get') as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.json.return_value = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [2.266667, 48.866667]
                        },
                        "properties": {
                            "label": "1 Boulevard Victor Hugo 75016 Paris",
                            "score": 0.9,
                            "postcode": "75016",
                            "city": "Paris",
                            "citycode": "75116",
                            "type": "housenumber"
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Call function
            validate_and_geocode_address("1 Boulevard Victor Hugo, Paris")
            
            # Assertions
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == "https://api-adresse.data.gouv.fr/search/"
            assert call_args[1]['params'] == {'q': '1 Boulevard Victor Hugo, Paris', 'limit': 1}
            assert call_args[1]['timeout'] == 5
