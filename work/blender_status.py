import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=r'C:\Users\takas\AppData\Local\hermes\bin\uv.exe', args=['--directory', r'C:\Users\takas\AppData\Local\BlenderMCP\blender_mcp\mcp', 'run', 'blender-mcp'])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.call_tool('execute_blender_code', {'code': "import bpy\nresult={'filepath': bpy.data.filepath, 'dirty': bpy.data.is_dirty, 'objects': [o.name for o in bpy.context.scene.objects], 'scene': bpy.context.scene.name}"})
            print(json.dumps(response.structuredContent, ensure_ascii=False))
            if response.isError:
                raise RuntimeError(str(response.content))
asyncio.run(main())
