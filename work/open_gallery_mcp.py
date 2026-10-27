import asyncio, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CODE = r'''import bpy
path = r"C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp\outputs\museum_walkthrough.blend"
names = sorted(o.name for o in bpy.context.scene.objects)
if bpy.data.filepath or bpy.data.is_dirty or names != ['Camera', 'Cube', 'Light']:
    result = {'scheduled': False, 'reason': 'Current Blender scene is no longer the clean default scene', 'filepath': bpy.data.filepath, 'dirty': bpy.data.is_dirty, 'objects': names}
else:
    def open_later(target=path):
        import bpy
        bpy.ops.wm.open_mainfile(filepath=target)
        return None
    bpy.app.timers.register(open_later, first_interval=1.0)
    result = {'scheduled': True, 'path': path}
'''

async def main():
    params=StdioServerParameters(command=r'C:\Users\takas\AppData\Local\hermes\bin\uv.exe',args=['--directory',r'C:\Users\takas\AppData\Local\BlenderMCP\blender_mcp\mcp','run','blender-mcp'])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            response=await asyncio.wait_for(session.call_tool('execute_blender_code',{'code':CODE}),30)
            print(json.dumps(response.structuredContent,ensure_ascii=False))
            if response.isError: raise RuntimeError(str(response.content))
asyncio.run(main())
