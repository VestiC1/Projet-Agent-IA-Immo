
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
from enum import Enum

class TypeBien(str, Enum):
    maison = "maison"
    appartement = "appartement"

con = duckdb.connect(BPE_INSEE_DB)

@tool
async def geocoding_tools(address: str) -> dict[str,float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    return await geocoding(address)

@tool
async def commune_info_tools(code_insee:str) -> dict[str, float]:
    """Obtenir les information sur les nombres d'équipement pour un code insee"""
    return get_commune_info(con, code_insee=code_insee)

@tool
async def recent_transactions_tools(code_insee:str, type_bien : TypeBien, n:int = 10) -> dict[str, float]:
    """Obtenir les informations sur les 10 transaction les plus récentes pour un code insee."""
    return await get_recent_transactions(code_insee=code_insee, type_bien=type_bien, top_n=n)

@tool
async def estimation_tools(address:str, type_local:str, surface_habitable:float, surface_terrain:float, nombre_pieces:int) -> dict[str,float]:
    """Obtenir une estimation sur le prix de vente d'une maison ou d'un appartement située à une adresse"""
    return estimate_price(address, type_local, surface_habitable, surface_terrain, nombre_pieces)

llm_mistral = ChatMistralAI(model="mistral-small-latest", api_key=api_key_mistral, temperature=0)
llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key_gemini, temperature=0)

agent = create_agent(
    model=llm_mistral,
    tools=[geocoding, commune_info_tools, recent_transactions_tools, estimation_tools],  # Pass the decorated tool directly
    system_prompt="""
        Vous êtes un agent immobilier virtuel qui aide les utilisateurs 
        à trouver des propriétés et estimer leur valeur.

        Outils disponibles :
        - geocoding_tools : convertit une adresse ou un nom de commune en coordonnées GPS, 
          et permet d'obtenir le code INSEE d'une commune à partir de son nom.
        - commune_info_tools : fournit des informations détaillées sur une commune 
          (nécessite un code INSEE, utilisez d'abord geocoding_tools si vous n'avez que le nom).
        - recent_transactions_tools : récupère les dernières transactions immobilières 
          pour un code INSEE donné, filtré par type de bien (maison, appartement, terrain).
        - estimation_tools : estime le prix de vente d'une maison ou d'un appartement 
          à une adresse donnée. Nécessite : adresse, type (maison/appartement uniquement), 
          surface habitable, surface terrain, nombre de pièces.
          Ne fonctionne PAS pour les terrains.

        Workflow typique :
        1. L'utilisateur mentionne une ville → geocoding_tools pour récupérer le code INSEE
        2. Avec le code INSEE → commune_info_tools pour les détails de la commune
        3. Pour les transactions → recent_transactions_tools avec le code INSEE et le type de bien
        4. Pour une estimation → demander à l'utilisateur les informations manquantes 
           (adresse, type, surface, pièces) puis appeler estimation_tools
     """
)


