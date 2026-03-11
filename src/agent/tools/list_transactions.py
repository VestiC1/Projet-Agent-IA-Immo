import asyncio
import math
import os
from datetime import datetime

import aiohttp
import diskcache
from shapely.geometry import shape

CACHE_DIR = os.getenv("DVF_CACHE_DIR", "./dvf_cache")
CACHE_TTL = 60 * 60 * 12  # 12h

cache = diskcache.Cache(CACHE_DIR)
SEM = asyncio.Semaphore(5)


def extract_centroid(geometry: dict) -> tuple[float, float] | None:
    try:
        centroid = shape(geometry).centroid
        return round(centroid.y, 6), round(centroid.x, 6)
    except Exception:
        return None


def filter_transaction(feature: dict) -> dict | None:
    p = feature["properties"]
    if p.get("libnatmut") != "Vente":
        return None
    codtypbien = p.get("codtypbien", "")
    if not (codtypbien.startswith("11") or codtypbien.startswith("12")):
        return None
    centroid = extract_centroid(feature["geometry"])
    return {
        "date_mutation": p.get("datemut"),
        "type_bien": p.get("libtypbien"),
        "surface_bati_m2": p.get("sbati"),
        "surface_terrain_m2": p.get("sterr"),
        "prix_euros": p.get("valeurfonc"),
        "latitude": centroid[0] if centroid else None,
        "longitude": centroid[1] if centroid else None,
    }


async def _fetch_page(
    session: aiohttp.ClientSession, url: str, params: dict, page: int
) -> list:
    async with SEM:
        page_params = {**params, "page": page}
        async with session.get(
            url, headers={"Accept": "application/json"}, params=page_params
        ) as response:
            response.raise_for_status()
            data = await response.json()
    return data["features"]


async def _fetch_all_pages(code_insee: str, type_bien: str) -> list[dict]:
    url = "https://apidf-preprod.cerema.fr/dvf_opendata/geomutations/"
    current_year = datetime.now().year

    cache_key = f"cerema:{code_insee}:{type_bien}:{current_year - 1}:{current_year}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    page_size = 500
    params = {
        "code_insee": code_insee,
        "codtypbien": type_bien,
        "idnatmut": 1,
        "anneemut_min": current_year - 3,
        "anneemut_max": current_year,
        "page_size": page_size,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers={"Accept": "application/json"}, params={**params, "page": 1}
        ) as response:
            response.raise_for_status()
            first = await response.json()

        total_pages = math.ceil(first["count"] / page_size)
        print(first["count"] , total_pages)
        all_features = first["features"]

        if total_pages > 1:
            tasks = [
                _fetch_page(session, url, params, page)
                for page in range(2, total_pages + 1)
            ]
            results = await asyncio.gather(*tasks)
            for page_features in results:
                all_features.extend(page_features)

    cache.set(cache_key, all_features, expire=CACHE_TTL)
    return all_features


async def get_recent_transactions(
    code_insee: str, type_bien: str = "11", top_n: int = 10
) -> list[dict]:
    all_features = await _fetch_all_pages(code_insee, type_bien)
    transactions = [f for f in (filter_transaction(f) for f in all_features) if f]
    return sorted(transactions, key=lambda t: t["date_mutation"], reverse=True)[:top_n]

async def main():
    results = await get_recent_transactions(
        code_insee='37261',
        type_bien="12",
        top_n = 10,   
    )

    print(len(results))

if __name__ == '__main__':
    cache.clear()
    asyncio.run(main())