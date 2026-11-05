import bpy
import sys
from pathlib import Path

output = str(Path(sys.argv[sys.argv.index('--') + 1]).resolve())
scene = bpy.context.scene
scene.frame_set(120)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.cycles.use_denoising = False
scene.render.resolution_x = 384
scene.render.resolution_y = 216
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output
bpy.ops.render.render(write_still=True)
