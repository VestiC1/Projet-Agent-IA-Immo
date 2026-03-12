import aiohttp

timeout = aiohttp.ClientTimeout(total=30)

async def geocoding(address: str) -> dict[str,float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    if not address or len(address) < 5:
        raise ValueError("Adresse invalide. Veuillez fournir une adresse complète.")

    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address, "limit": 1}

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
    except aiohttp.ClientError as e:
        raise RuntimeError(f"Erreur lors de la requête à l'API de géocodage : {e}")
    
    coords = data['features'][0]['geometry']['coordinates']
    address_returned = data['features'][0]['properties']['label']
    code_insee = data['features'][0]['properties']['citycode']
    type_voie = data['features'][0]['properties'].get('street')
    type_voie = type_voie.split()[0] if type_voie else None
    return {"adresse": address_returned, "code_insee": code_insee, "type_voie": type_voie, "longitude": coords[0], "latitude": coords[1]}
