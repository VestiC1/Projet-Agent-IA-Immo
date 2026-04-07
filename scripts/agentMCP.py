import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp")

async def call_tool(tool: str, name: str):
    async with client:
        result = await client.call_tool(tool, {"name": name})
        print(result)

asyncio.run(call_tool("geocoding_tools", "49 blvd preuilly, 37000 Tours"))
asyncio.run(call_tool("commune_info_tools", "37261"))
#asyncio.run(call_tool("recent_transactions_tools", "37261", "maison", 10))

