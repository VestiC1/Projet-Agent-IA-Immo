
from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

from src.agents.tools.geocoding import geocoding
from config_agent import api_key_mistral, api_key_gemini

@tool
async def geocoding_tools(address: str) -> dict[str,float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    return await geocoding(address)

llm_mistral = ChatMistralAI(model="mistral-small-latest", api_key=api_key_mistral, temperature=0)
llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key_gemini, temperature=0)

agent = create_agent(
    model=llm_mistral,
    tools=[geocoding],  # Pass the decorated tool directly
    system_prompt="""Vous êtes un agent immobilier virtuel qui aide les utilisateurs 
     à trouver des propriétés en utilisant des coordonnées géographiques.
     Utilisez l'outil geocoding pour obtenir les coordonnées à partir d'une adresse.
     Lorsque vous recevez une question, utilisez l'outil pour obtenir les coordonnées
     de l'adresse fournie, puis répondez avec les coordonnées correspondantes."""
)


