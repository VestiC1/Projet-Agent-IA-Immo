from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from config import BPE_INSEE_DB
from src.agents.tools.geocoding import geocoding
from src.agents.tools.commune_info import get_commune_info
from src.agents.tools.list_transactions import get_recent_transactions
from src.agents.tools.do_prediction import estimate_price
from config_agent import api_key_mistral, api_key_gemini
from typing import Union
import duckdb
import aiohttp
import asyncio
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class TypeBien(str, Enum):
    maison = "maison"
    appartement = "appartement"

con = duckdb.connect(BPE_INSEE_DB)

# ── Retry decorator pour les appels réseau ────────────────────────────────
network_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ConnectionError,
    )),
    reraise=True,
)


@tool
@network_retry
async def geocoding_tools(address: str) -> dict[str, float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    if not address or len(address.strip()) < 2:
        return {"error": "Adresse invalide. Veuillez fournir une adresse plus précise."}
    try:
        return await geocoding(address)
    except (aiohttp.ClientError, asyncio.TimeoutError):
        raise  # laisse tenacity retry
    except Exception as e:
        return {"error": f"Geocoding échoué: {type(e).__name__}: {e}"}


@tool
async def commune_info_tools(code_insee: str) -> dict[str, float]:
    """Obtenir les informations sur les nombres d'équipement pour un code INSEE."""
    if not code_insee or not code_insee.strip().isdigit() or len(code_insee.strip()) != 5:
        return {"error": f"Code INSEE invalide: '{code_insee}'. Attendu: 5 chiffres (ex: 37261)."}
    try:
        result = get_commune_info(con, code_insee=code_insee)
        if not result:
            return {"error": f"Aucune donnée trouvée pour le code INSEE {code_insee}."}
        return result
    except duckdb.Error as e:
        return {"error": f"Erreur base de données: {e}"}
    except Exception as e:
        return {"error": f"Commune info échoué: {type(e).__name__}: {e}"}


@tool
@network_retry
async def recent_transactions_tools(code_insee: str, type_bien: TypeBien, n: int = 10) -> dict[str, float]:
    """Obtenir les informations sur les 10 transactions les plus récentes pour un code INSEE."""
    if not code_insee or not code_insee.strip().isdigit() or len(code_insee.strip()) != 5:
        return {"error": f"Code INSEE invalide: '{code_insee}'. Attendu: 5 chiffres (ex: 37261)."}
    if n < 1 or n > 50:
        n = min(max(n, 1), 50)
    try:
        result = await get_recent_transactions(code_insee=code_insee, type_bien=type_bien, top_n=n)
        if not result:
            return {"error": f"Aucune transaction trouvée pour {code_insee} ({type_bien})."}
        return result
    except (aiohttp.ClientError, asyncio.TimeoutError):
        raise  # laisse tenacity retry
    except Exception as e:
        return {"error": f"Transactions échoué: {type(e).__name__}: {e}"}


@tool
async def estimation_tools(
    address: str,
    type_local: str,
    surface_habitable: float,
    surface_terrain: float,
    nombre_pieces: int,
) -> dict[str, float]:
    """Obtenir une estimation sur le prix de vente d'une maison ou d'un appartement située à une adresse."""
    # Validation des inputs
    if type_local not in ("maison", "appartement"):
        return {"error": f"Type '{type_local}' non supporté. Utilisez 'maison' ou 'appartement'."}
    if surface_habitable <= 0:
        return {"error": "La surface habitable doit être supérieure à 0."}
    if nombre_pieces < 1:
        return {"error": "Le nombre de pièces doit être au moins 1."}
    if not address or len(address.strip()) < 2:
        return {"error": "Adresse invalide."}
    try:
        return estimate_price(address, type_local, surface_habitable, surface_terrain, nombre_pieces)
    except Exception as e:
        return {"error": f"Estimation échouée: {type(e).__name__}: {e}"}


llm_mistral = ChatMistralAI(model="mistral-small-latest", api_key=api_key_mistral, temperature=0)
llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key_gemini, temperature=0)

agent = create_agent(
    model=llm_mistral,
    tools=[geocoding_tools, commune_info_tools, recent_transactions_tools, estimation_tools],
    system_prompt="""
        Vous êtes un agent immobilier virtuel qui aide les utilisateurs 
        à trouver des propriétés et estimer leur valeur.

        Outils disponibles :
        - geocoding_tools : convertit une adresse ou un nom de commune en coordonnées GPS, 
          et permet d'obtenir le code INSEE d'une commune à partir de son nom.
        - commune_info_tools : fournit des informations détaillées sur une commune 
          (nécessite un code INSEE, utilisez d'abord geocoding_tools si vous n'avez que le nom).
        - recent_transactions_tools : récupère les dernières transactions immobilières 
          pour un code INSEE donné, filtré par type de bien (maison, appartement).
        - estimation_tools : estime le prix de vente d'une maison ou d'un appartement 
          à une adresse donnée. Nécessite : adresse, type (maison/appartement uniquement), 
          surface habitable, surface terrain, nombre de pièces.
          Ne fonctionne PAS pour les terrains.

        Gestion des erreurs :
        - Si un outil retourne un champ "error", expliquez le problème à l'utilisateur 
          et proposez une alternative (reformuler, vérifier l'adresse, etc.).
        - Ne réinventez jamais de données. Si un outil échoue, dites-le clairement.

        Workflow typique :
        1. L'utilisateur mentionne une ville → geocoding_tools pour récupérer le code INSEE
        2. Avec le code INSEE → commune_info_tools pour les détails de la commune
        3. Pour les transactions → recent_transactions_tools avec le code INSEE et le type de bien
        4. Pour une estimation → demander à l'utilisateur les informations manquantes 
           (adresse, type, surface, pièces) puis appeler estimation_tools
     """
)