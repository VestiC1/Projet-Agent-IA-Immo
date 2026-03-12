import asyncio
from src.agents import agent_immo, AgentContext


async def main() -> None:
    question : str = "Quelle est la latitude et la longitude du 49 Bd Preuilly, 37000 Tours, France?"
    
    # si plusieurs conversations, on définit le nom du thread correspondant à la conversation en cours
    # Utiliser par langgraph pour l'historique des conversations (checkpointer))
    config = {"configurable": {"thread_id": "conversation_1"}} 
    
    response = await agent_immo.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
        context=AgentContext(user_id="1")
    )
    msg_final = response["messages"][-1].content

    print(f"question utilisateur : {question}")
    print()
    print(f"reponse utilisateur : {msg_final}")

    response = await agent_immo.ainvoke(
    {"messages": [{"role": "user", "content": "Quelle est la latitude et la longitude du 8 rue du paradis, 37360 Rouziers de Touraine France?"}]},
    config=config,
    context=AgentContext(user_id="1")
    )
    msg_final = response["messages"][-1].content

    print(f"question utilisateur : {question}")
    print()
    print(f"reponse utilisateur : {msg_final}")

    #config = {"configurable": {"thread_id": "conversation_2"}} # Pour tester si ca marche on le fait basculer sur un autre thread de conversation
    response = await agent_immo.ainvoke(
    {"messages": [{"role": "user", "content": "Quelle est le nombre d'equipements de la commune de ces deux adresses ?"}]},
    config=config,
    context=AgentContext(user_id="1")
    )
    msg_final = response["messages"][-1].content

    print(f"question utilisateur : {question}")
    print()
    print(f"reponse utilisateur : {msg_final}")


if __name__ == "__main__":
    asyncio.run(main())