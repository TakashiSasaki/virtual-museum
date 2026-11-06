"""Render the three added storage assets without saving preview staging."""
from pathlib import Path

import bpy
from mathutils import Vector

source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend':
    raise RuntimeError('Open the saved V1 workshop')
repo = source.resolve().parents[2]
scene = bpy.data.scenes['Museum V1 | Asset workshop']
bpy.context.window.scene = scene
names = ('LabDrawerCabinet', 'LabUtilityCart', 'LabTallCabinet')
roots = [bpy.data.objects.get(n) for n in names]
if not all(roots):
    raise RuntimeError('Create the storage assets first')
visible = set(roots)
for root in roots:
    visible.update(root.children_recursive)
for obj in scene.objects:
    obj.hide_render = obj not in visible
for root, position in zip(roots, ((-1.02, -.17, 0), (-.24, -.06, 0), (.91, .25, 0))):
    root.location = position
roots[0].rotation_euler.z = -.07
roots[1].rotation_euler.z = .06

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.002))
floor = bpy.context.object
floor.name = 'Storage preview ground'
mat = bpy.data.materials.new('Storage preview neutral ground')
mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (.43, .45, .44, 1)
bsdf.inputs['Roughness'].default_value = .72
floor.data.materials.append(mat)
scene.world = bpy.data.worlds.new('Storage preview world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.53, .57, .60, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .32
for location, energy, size in [((-3.2, -4.1, 5.0), 650, 4.0),
                              ((3.4, -.8, 4.2), 430, 3.3),
                              ((.2, 3.0, 4.1), 420, 2.6)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.data.energy, light.data.size = energy, size
    light.rotation_euler = (Vector((0, 0, .8))-light.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(location=(3.15, -6.8, 3.18))
cam = bpy.context.object
cam.rotation_euler = (Vector((.0, .06, .91))-cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 3.2
scene.camera = cam
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1400, 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
output = repo / 'blender/previews/lab_storage.png'
output.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
print('LAB_STORAGE_PREVIEW', output.name)
# Do not save: leave the asset workshop's display, lighting and camera intact.
