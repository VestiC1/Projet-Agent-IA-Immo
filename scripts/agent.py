
from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
import aiohttp
import asyncio

from config_agent import api_key_mistral, api_key_gemini

@tool
async def geocoding(address: str) -> dict[str,float]:
    """Obtenir les coordonnées géographiques pour une adresse donnée."""
    if not address or len(address) < 5:
        raise ValueError("Adresse invalide. Veuillez fournir une adresse complète.")

    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address, "limit": 1}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
    except aiohttp.ClientError as e:
        raise RuntimeError(f"Erreur lors de la requête à l'API de géocodage : {e}")
    
    coords = data['features'][0]['geometry']['coordinates']
    address_returned = data['features'][0]['properties']['label']
    code_insee = data['features'][0]['properties']['citycode']
    type_voie = data['features'][0]['properties']['street'].split()[0]
    return {"adresse": address_returned, "code_insee": code_insee, "type_voie": type_voie, "longitude": coords[0], "latitude": coords[1]}

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

async def main() -> None:
    question : str = "Quelle est la latitude et la longitude du 49 Bd Preuilly, 37000 Tours, France?"
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    msg_final = response["messages"][-1].content

    print(f"question utilisateur : {question}")
    print()
    print(f"reponse utilisateur : {msg_final}")

if __name__ == "__main__":
    asyncio.run(main())
