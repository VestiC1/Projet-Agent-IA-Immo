from dotenv import load_dotenv
import os
from langchain.agents import create_agent
from langchain_mistralai import ChatMistralAI 
import aiohttp
import asyncio

# Retrieve API key from environment variable
load_dotenv()
api_key_mistral = os.getenv("MISTRAL_API_KEY")
print(f"API Key Mistral: {api_key_mistral}")  # Debug print to verify the API key is loaded
# Initialize the Mistral LLM
llm_mistral = ChatMistralAI(model="mistral-small-latest", api_key=api_key_mistral, temperature=0)

async def get_geocodage(address: str) -> tuple[float, float]:
    
    # Check if the address is valid
    if not address or len(address) < 5: # address length could be adjusted
        raise ValueError("Adresse invalide. Veuillez fournir une adresse complète.")

    # Parameters for the geocoding API
    url = f"https://api-adresse.data.gouv.fr/search/"
    params = {
        "q": address,
        "limit": 1
    }



    # API request
    try :
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            response.raise_for_status()  
                            data = await response.json()
    except aiohttp.ClientError as e:
        raise RuntimeError(f"Erreur lors de la requête à l'API de géocodage : {e}")
    
                        
    return data['features'][0]['geometry']['coordinates']  # Retourne les coordonnées (longitude, latitude)     

    

agent = create_agent(
    model = llm_mistral,
    tools = [
        {
            "name": "geocoding",
            "function": get_geocodage,
            "description": "Obtenir les coordonnées géographiques pour une adresse donnée."
        }
    ],
    system_prompt = """Vous êtes un agent immobilier virtuel qui aide les utilisateurs 
     à trouver des propriétés en utilisant des coordonnées géographiques.

     Utilisez l'outil de géocodage get_geocodage pour obtenir les coordonnées à partir d'une 
    adresse.
    
        Lorsque vous recevez une question de l'utilisateur, utilisez l'outil de géocodage pour
    obtenir les coordonnées de l'adresse fournie, puis répondez à l'utilisateur avec les
    coordonnées correspondantes.
    """   
)

async def main() -> None:
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Quelle est la latitude et la longitude du 49 Bd Preuilly, 37000 Tours, France?"}]}
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())


