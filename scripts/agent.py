import asyncio
from src.agents import agent_immo

async def main() -> None:
    question : str = "Quelle est la latitude et la longitude du 49 Bd Preuilly, 37000 Tours, France?"
    response = await agent_immo.ainvoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    msg_final = response["messages"][-1].content

    print(f"question utilisateur : {question}")
    print()
    print(f"reponse utilisateur : {msg_final}")

if __name__ == "__main__":
    asyncio.run(main())