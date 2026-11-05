import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command=r"C:\Users\takas\AppData\Local\hermes\bin\uv.exe",
        args=["--directory", r"C:\Users\takas\AppData\Local\BlenderMCP\blender_mcp\mcp", "run", "blender-mcp"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await asyncio.wait_for(session.initialize(), 30)
            tools = await asyncio.wait_for(session.list_tools(), 30)
            print("server:", init.serverInfo.name, init.serverInfo.version)
            print("tools:", ", ".join(tool.name for tool in tools.tools))
            result = await asyncio.wait_for(session.call_tool("get_objects_summary", arguments={}), 30)
            print("scene_summary:", result.model_dump_json())
            if result.isError:
                raise RuntimeError("Blender scene summary failed")

asyncio.run(main())
