"""Render the saved specimen-box materials and details without saving the blend.

Run in a separate background Blender process on museum_v1_assets.blend.
Only the specimen shelf is shown; the workshop and its camera remain unchanged
on disk. The view includes all fourteen drawers and the inclined display trays.
"""
from pathlib import Path

import bpy
from mathutils import Vector

source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend':
    raise RuntimeError('Open the V1 asset workshop before rendering')
repo = source.resolve().parents[2]
scene = bpy.data.scenes['Museum V1 | Asset workshop']
bpy.context.window.scene = scene
root = bpy.data.objects['SpecimenShelf']
parts = set(root.children_recursive)
for obj in scene.objects:
    obj.hide_render = obj != root and obj not in parts
root.location = (0, 0, 0)


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return mat


bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.004))
floor = bpy.context.object
floor.name = 'Specimen shelf preview ground'
floor.data.materials.append(material('Specimen shelf preview ground', (.42, .43, .41), .9))

for location, energy, size in [((-3, -4, 5), 480, 3),
                              ((3, -1.5, 3.5), 300, 2.5),
                              ((0, 3, 4), 350, 2.5)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 1.7)) - light.location).to_track_quat('-Z', 'Y').to_euler()
scene.world = bpy.data.worlds.new('Specimen shelf preview world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.50, .53, .55, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35

bpy.ops.object.camera_add(location=(2.1, -6, 3.1))
camera = bpy.context.object
camera.name = 'Specimen shelf preview camera'
camera.rotation_euler = (Vector((0, 0, 1.72)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.9
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
output = repo / 'blender/previews/specimen_boxes_detail.png'
output.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
print('SPECIMEN_SHELF_PREVIEW', output.name)
# Deliberately no save: preserve all workshop object, lighting and camera state.
