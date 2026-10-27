from PIL import Image, ImageDraw
from pathlib import Path
work=Path(r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp\work')
frames=[1,100,180,260,350,450,540,640,740,840]
canvas=Image.new('RGB',(1500,660),'#eeeeee'); draw=ImageDraw.Draw(canvas)
for i,frame in enumerate(frames):
    im=Image.open(work/f'walk-{frame:04d}.png').convert('RGB'); im.thumbnail((290,280))
    x=(i%5)*300; y=(i//5)*330
    canvas.paste(im,(x+(300-im.width)//2,y+25)); draw.text((x+8,y+5),f'Frame {frame}',fill='black')
canvas.save(work/'walk-contact.jpg',quality=90)
