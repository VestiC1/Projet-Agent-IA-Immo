
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
    address_rebuilt = data['features'][0]['properties']['label']
    code_insee = data['features'][0]['properties']['citycode']
    type_voie = data['features'][0]['properties']['street'].split()[0]
    
    return {"adresse": address_rebuilt, "code_insee": code_insee, "longitude": coords[0], "latitude": coords[1], "type_voie": type_voie}

llm_mistral = ChatMistralAI(model="mistral-small-latest", api_key=api_key_mistral, temperature=0, max_tokens=1000)
llm_gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key_gemini, temperature=0, max_tokens=1000)

agent = create_agent(
    model=llm_mistral,
    tools=[geocoding],  # Pass the decorated tool directly
    system_prompt="""Vous êtes un agent immobilier virtuel qui aide les utilisateurs 
     à trouver des propriétés en utilisant des coordonnées géographiques.
     Utilisez l'outil geocoding pour obtenir soit les coordonnées (longitude et latitude) à partir d'une adresse,
     son adresse reconstruite soit le code INSEE de la commune correspondante.
     Lorsque vous recevez une question demandant les coordonnées, le code insee ou le type de voie,
     tu appelleras l'outil geocoding et retourneras **toujours** toutes les informations suivantes :
     l'adresse reconstruite, le code insee de la ville, les coordonnées et le type de voie.
     Si l'appel à l'outil geocoding n'est pas nécessaire, tu répondras à la question sans l'utiliser.
     """
)



async def main() -> None:
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Quelle est sont les coordonnees du 10 rue de la paix à Paris?"}]}
    )
    final_msg = response["messages"][-1]
    print(final_msg.content)

if __name__ == "__main__":
    asyncio.run(main())
