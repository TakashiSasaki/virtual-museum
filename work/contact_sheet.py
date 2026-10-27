from PIL import Image, ImageOps, ImageDraw
from pathlib import Path

source = Path(r'C:\Users\takas\.codex\attachments\0ca8192d-80d5-4298-b360-e506eed0f819')
out = Path(r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp\work')
for start, end in [(1, 10), (11, 19)]:
    canvas = Image.new('RGB', (1500, ((end-start)//3+1)*320), '#eeeeee')
    draw = ImageDraw.Draw(canvas)
    for idx in range(start, end+1):
        im = Image.open(source / f'image-{idx}.png').convert('RGB')
        im.thumbnail((490, 280))
        pos = idx-start
        x, y = (pos%3)*500, (pos//3)*320
        canvas.paste(im, (x+(500-im.width)//2, y+25))
        draw.text((x+8,y+5), f'Image {idx}', fill='black')
    canvas.save(out / f'contact-{start}-{end}.jpg', quality=90)
