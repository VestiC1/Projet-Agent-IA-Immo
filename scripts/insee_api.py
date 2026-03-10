import requests
from typing import Optional
from functools import lru_cache


class DensitePopulation:
    """Récupère la densité de population"""
    
    BASE_URL = "https://geo.api.gouv.fr"
    
    def __init__(self):
        self.session = requests.Session()
    
    @lru_cache(maxsize=500)
    def _get_data(self, citycode: str) -> Optional[tuple[int, float]]:
        """Récupère population et surface (avec cache)"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/communes/{citycode}",
                params={"fields": "population,surface"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get('population', 0), data.get('surface', 0)
        except:
            return None
    
    @lru_cache(maxsize=500)
    def _get_arrondissement(self, lat: float, lon: float) -> Optional[tuple[int, float]]:
        """Récupère arrondissement via GPS"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/communes",
                params={"lat": lat, "lon": lon, "fields": "code,population,surface"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                code = data[0].get('code', '')
                if (code.startswith('751') or code.startswith('132') or 
                    (code.startswith('69') and len(code) == 5)):
                    return data[0].get('population', 0), data[0].get('surface', 0)
            return None
        except:
            return None
    
    def get_densite(self, geocode_data: dict) -> Optional[float]:
        """
        Retourne la densité de population en hab/km²
        
        Args:
            geocode_data: Résultat de validate_and_geocode_address
        
        Returns:
            float: Densité en hab/km² ou None
        """
        if not geocode_data or not geocode_data.get('citycode'):
            return None
        
        # Essayer arrondissement
        data = None
        if geocode_data.get('latitude') and geocode_data.get('longitude'):
            data = self._get_arrondissement(
                geocode_data['latitude'],
                geocode_data['longitude']
            )
        
        # Sinon commune
        if not data:
            data = self._get_data(geocode_data['citycode'])
        
        if not data:
            return None
        
        population, surface = data
        if surface == 0:
            return 0
        
        # La surface est déjà en hectares, donc diviser par 100 pour avoir des km²
        return round(population / (surface / 100), 2)


# Utilisation
if __name__ == "__main__":
    import requests
    
    def validate_and_geocode_address(address: str) -> tuple[bool, Optional[dict]]:
        if not address or len(address) < 5:
            return False, None
        
        try:
            response = requests.get(
                "https://api-adresse.data.gouv.fr/search/",
                params={'q': address, 'limit': 1},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                return False, None
            
            feature = data['features'][0]
            geocode_data = {
                'latitude': feature['geometry']['coordinates'][1],
                'longitude': feature['geometry']['coordinates'][0],
                'citycode': feature['properties'].get('citycode'),
                'score': feature['properties'].get('score', 0)
            }
            
            return geocode_data['score'] >= 0.5, geocode_data
        except:
            return False, None
    
    # Test
    densite_api = DensitePopulation()
    
    addresses = [
        "10 Place Jean Jaurès, 37000 Tours",
        "Tour Eiffel, 75007 Paris",
        "Place Bellecour, 69002 Lyon",
        "amboise, 37400",
        "Saint-Paterne-Racan, 37370"
    ]
    
    for addr in addresses:
        is_valid, geocode = validate_and_geocode_address(addr)
        if is_valid:
            densite = densite_api.get_densite(geocode)
            print(f"{addr}: {densite:,.0f} hab/km²")