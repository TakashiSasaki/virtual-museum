"""Preview the saved laboratory seats in a separate process; never save setup."""
from pathlib import Path
import bpy
from mathutils import Vector

source=Path(bpy.data.filepath)
if source.name!='museum_v1_assets.blend':
    raise RuntimeError('Open the V1 asset workshop for this preview')
repo=source.resolve().parents[2]
scene=bpy.data.scenes['Museum V1 | Asset workshop']
bpy.context.window.scene=scene
chair=bpy.data.objects['LabSwivelChair']
stool=bpy.data.objects['LabRoundStool']
visible={chair,stool,*chair.children_recursive,*stool.children_recursive}
for obj in scene.objects:
    obj.hide_render=obj not in visible
chair.location=(-.40,0,0)
chair.rotation_euler.z=-.20
stool.location=(.47,.08,0)

bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002))
floor=bpy.context.object
mat=bpy.data.materials.new('Preview laboratory floor')
mat.use_nodes=True
p=mat.node_tree.nodes['Principled BSDF']
p.inputs['Base Color'].default_value=(.53,.55,.53,1)
p.inputs['Roughness'].default_value=.62
floor.data.materials.append(mat)
scene.world=bpy.data.worlds.new('Laboratory seating preview world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.38,.42,.46,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.34
for position,energy,size in [((-1.5,-2.2,3.2),240,2.1),((2,-.4,2.3),160,1.6),((0,2,2.4),200,1.8)]:
    bpy.ops.object.light_add(type='AREA',location=position)
    light=bpy.context.object
    light.data.energy=energy
    light.data.shape='DISK'
    light.data.size=size
    light.rotation_euler=(Vector((0,0,.45))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.1,-3.5,2.1))
camera=bpy.context.object
camera.rotation_euler=(Vector((.03,0,.43))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'
camera.data.ortho_scale=1.73
scene.camera=camera
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1400
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
output=repo/'blender/previews/lab_seating.png'
scene.render.filepath=str(output)
bpy.ops.render.render(write_still=True)
print('LAB_SEATING_PREVIEW',output.name)
# No save: this staging belongs only to the preview process.
