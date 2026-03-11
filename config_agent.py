from dotenv import load_dotenv
import os

load_dotenv(override=True)

api_key_mistral = os.getenv("MISTRAL_API_KEY")
if not api_key_mistral: 
    raise ValueError("Clé API Mistral manquante. Veuillez définir la variable d'environnement MISTRAL_API_KEY.")

api_key_gemini = os.getenv("GEMINI_API_KEY")
if not api_key_gemini:
    raise ValueError("Clé API Gemini manquante. Veuillez définir la variable d'environnement GEMINI_API_KEY.")
