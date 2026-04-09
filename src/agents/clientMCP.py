from langchain_mcp_adapters.client import MultiServerMCPClient


async def create_client():
    # 1. Récupérer les outils MCP
    return MultiServerMCPClient(
        {
            "outils_immo": {
                "transport": "http",
                "url": "http://localhost:8100/mcp",  # Préfixe /mcp confirmé
            }
        }
    )

    tools = await client.get_tools()
    print("Outils MCP disponibles :", list(tools.keys()))

    # 2. Créer l'agent avec les outils MCP et le LLM existant
    agent = create_immobilier_agent(list(tools.values()))

    # 3. Exemples d'utilisation
    response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Quelles sont les coordonnées GPS de '1 rue de Paris, Paris' ?"
        }]
    })
    print("Réponse agent :", response)
