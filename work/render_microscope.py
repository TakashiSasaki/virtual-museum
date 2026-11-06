"""Render the saved refined microscope without saving preview setup to the blend.

Run in a separate Blender process on blender/scenes/museum_v1_assets.blend.
The green workmat is preview staging; the actual Unity bench already has its mat.
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
root = bpy.data.objects['Microscope']
parts = set(root.children_recursive)
for obj in scene.objects:
    obj.hide_render = obj != root and obj not in parts
root.location = (0, 0, 0)


def material(name, color, roughness):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    return m


def block(name, center, size, mat, bevel):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new('Preview edges', 'BEVEL')
    mod.width = bevel
    mod.segments = 3
    obj.modifiers.new('Preview face normals', 'WEIGHTED_NORMAL')


mat = material('Preview green benchmat', (.035, .19, .145), .69)
block('Preview green benchmat', (0, -.015, -.006), (.63, .56, .011), mat, .006)
block('Preview laboratory bench', (0, 0, -.025), (200, 200, .030),
      material('Preview warm white bench', (.75, .77, .73), .46), .003)

for location, energy, size in [((-.7, -1.0, 1.25), 65, .95),
                              ((.85, .1, .95), 42, .8),
                              ((-.25, .9, .75), 33, .7)]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, .33))-light.location).to_track_quat('-Z', 'Y').to_euler()
scene.world = bpy.data.worlds.new('Microscope preview world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.40, .44, .47, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25

bpy.ops.object.camera_add(location=(.75, -1.35, .84))
camera = bpy.context.object
camera.name = 'Microscope preview camera'
camera.rotation_euler = (Vector((0, -.005, .32))-camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = .82
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
output = repo / 'blender/previews/microscope_detail.png'
output.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
print('MICROSCOPE_PREVIEW', output.name)
# Deliberately no save: retain the workshop's original lighting and camera.
