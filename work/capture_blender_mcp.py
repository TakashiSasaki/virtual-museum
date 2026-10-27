import asyncio,base64,os
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    params=StdioServerParameters(command=r'C:\Users\takas\AppData\Local\hermes\bin\uv.exe',args=['--directory',r'C:\Users\takas\AppData\Local\BlenderMCP\blender_mcp\mcp','run','blender-mcp'])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            res=await asyncio.wait_for(session.call_tool('get_screenshot_of_window_as_image',{}),40)
            if res.isError: raise RuntimeError(str(res.content))
            image=next((c for c in res.content if c.type=='image'),None)
            if image is None: raise RuntimeError('No image was returned')
            target=r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp\work\blender-window.png'
            with open(target,'wb') as f: f.write(base64.b64decode(image.data))
            print('captured',target,os.path.getsize(target))
asyncio.run(main())
