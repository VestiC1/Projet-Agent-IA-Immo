"""
Test data fixtures for the real estate prediction API.
"""
import pytest


@pytest.fixture
def sample_valid_addresses():
    """Return a list of valid French addresses for testing."""
    return [
        "1 Boulevard Victor Hugo, 75016 Paris",
        "10 Rue de Rivoli, 75004 Paris",
        "5 Avenue des Champs-Élysées, 75008 Paris",
        "15 Place de la République, 75011 Paris"
    ]


@pytest.fixture
def sample_invalid_addresses():
    """Return a list of invalid addresses for testing."""
    return [
        "",
        "123",
        "Invalid Street Name",
        "123 Fake Street, Fake City",
        "This is not a real address at all"
    ]


@pytest.fixture
def sample_property_data():
    """Return sample property data for testing."""
    return {
        "appartement": {
            "type_local": "Appartement",
            "surface_habitable": 80.0,
            "nombre_pieces": 3,
            "surface_terrain": 100.0
        },
        "maison": {
            "type_local": "Maison",
            "surface_habitable": 150.0,
            "nombre_pieces": 5,
            "surface_terrain": 500.0
        },
        "studio": {
            "type_local": "Studio",
            "surface_habitable": 30.0,
            "nombre_pieces": 1,
            "surface_terrain": 0.0
        }
    }


@pytest.fixture
def expected_geocoding_response():
    """Return expected geocoding response structure."""
    return {
        'address': str,
        'latitude': float,
        'longitude': float,
        'postcode': str,
        'city': str,
        'citycode': str,
        'type': str,
        'score': float
    }


@pytest.fixture
def expected_prediction_response():
    """Return expected prediction response structure."""
    return {
        'input': {
            'type': str,
            'address': str,
            'surface_habitable': float,
            'nombre_pieces': int,
            'surface_terrain': float
        },
        'coordinates': {
            'latitude': float,
            'longitude': float,
            'commune': str
        },
        'estimation': {
            'price': float,
            'price_per_m2': int,
            'confidence_interval': {
                'min': float,
                'max': float
            },
            'confidence_level': str
        },
        'metadata': {
            'address_score': float,
            'address_type': str
        }
    }


@pytest.fixture
def mock_geocoding_api_response():
    """Return mock geocoding API response."""
    return {
        "type": "FeatureCollection",
        "version": "draft",
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
                    "housenumber": "1",
                    "id": "75116_6059_00001",
                    "name": "Boulevard Victor Hugo",
                    "postcode": "75016",
                    "citycode": "75116",
                    "x": 652251.51,
                    "y": 6861892.66,
                    "city": "Paris",
                    "district": "Paris 16e Arrondissement",
                    "context": "75, Paris, Île-de-France",
                    "type": "housenumber",
                    "importance": 0.71201,
                    "street": "Boulevard Victor Hugo"
                }
            }
        ],
        "attribution": "BAN",
        "licence": "ETALAB-2.0",
        "query": "1 Boulevard Victor Hugo, Paris",
        "limit": 1
    }
