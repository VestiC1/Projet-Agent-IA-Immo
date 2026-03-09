import requests
from typing import Optional

def validate_and_geocode_address(address: str) -> tuple[bool, Optional[dict]]:
    """Validate French address using API Adresse"""
    if not address or len(address) < 5:
        return False, None
    
    try:
        url = "https://api-adresse.data.gouv.fr/search/"
        params = {'q': address, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('features') or len(data['features']) == 0:
            return False, None
        
        feature = data['features'][0]
        
        geocode_data = {
            'address': feature['properties']['label'],
            'latitude': feature['geometry']['coordinates'][1],
            'longitude': feature['geometry']['coordinates'][0],
            'postcode': feature['properties'].get('postcode'),
            'city': feature['properties'].get('city'),
            'citycode': feature['properties'].get('citycode'),
            'type': feature['properties'].get('type'),
            'score': feature['properties'].get('score', 0)
        }
        
        is_valid = geocode_data['score'] >= 0.5
        return is_valid, geocode_data
        
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return False, None