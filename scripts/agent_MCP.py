import asyncio
from fastmcp import Client

client = Client("http://localhost:8100/mcp")


async def call_tool(tool : str, args : dict):
    async with client:
        result = await client.call_tool(tool, args)
        print(result)


asyncio.run(call_tool("commune_info_tools", {"code_insee": "37261"}))
