from fastmcp import FastMCP
import duckdb
from config import BPE_INSEE_DB
from enum import Enum

from src.agents.tools.geocoding import geocoding
from src.agents.tools.commune_info import get_commune_info
from src.agents.tools.list_transactions import get_recent_transactions
from src.agents.tools.do_prediction import estimate_price


class TypeBien(str, Enum):
    maison = "maison"
    appartement = "appartement"

con = duckdb.connect(BPE_INSEE_DB)

mcp = FastMCP(
    "OutilsImmo",
    instructions="Fournis des outils pour aider à la prédiction de valeurs immobilières. Utilise ces outils pour répondre aux questions et fournir des informations pertinentes sur le marché immobilier.",
)

@mcp.tool
async def geocoding_tools(address: str) -> dict[str, float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    return await geocoding(address)

@mcp.tool
async def commune_info_tools(code_insee: str) -> dict[str, float]:
    """Obtenir les informations sur les nombres d'équipement pour un code INSEE."""
    return get_commune_info(con, code_insee=code_insee)

@mcp.tool
async def recent_transactions_tools(code_insee: str, type_bien: TypeBien, n: int = 10) -> dict[str, float]:
    """Obtenir les transactions récentes pour un code INSEE et type de bien."""
    return get_recent_transactions(code_insee=code_insee, type_bien=type_bien, top_n=n)

@mcp.tool
async def estimation_tools(
    address: str,
    type_local: str,
    surface_habitable: float,
    surface_terrain: float,
    nombre_pieces: int,
) -> dict[str, float]:
    """Estimer le prix d'un bien immobilier en fonction de ses caractéristiques."""
    return estimate_price(
        address=address,
        type_local=type_local,
        surface_habitable=surface_habitable,
        surface_terrain=surface_terrain,
        nombre_pieces=nombre_pieces,
    )
