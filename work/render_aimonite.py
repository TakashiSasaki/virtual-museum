"""Render Aimonite review views without saving changes to the workshop scene.

Run Blender on blender/scenes/museum_v1_assets.blend with this script.
Optional arguments after -- are view names, e.g. back back_angle.
"""
import bpy
import sys
from pathlib import Path
from mathutils import Vector

source=Path(bpy.data.filepath)
if source.name!='museum_v1_assets.blend':
    raise RuntimeError('Open the V1 asset workshop before rendering')
repo=source.resolve().parents[2]
scene=bpy.context.scene
root=bpy.data.objects['Aimonite']
for obj in scene.objects:
    if obj.type not in {'CAMERA','LIGHT'}:
        obj.hide_render=obj!=root and obj not in root.children_recursive
root.location=(0,0,0)
for obj in scene.objects:
    if obj.type=='LIGHT':obj.hide_render=True

for pos,power,size in [((-3,-4,5),650,4),((3,2,4),700,3),((-3,4,2.5),450,3)]:
    bpy.ops.object.light_add(type='AREA',location=pos)
    lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size
    lamp.rotation_euler=(Vector((0,0,1.2))-lamp.location).to_track_quat('-Z','Y').to_euler()

scene.world=bpy.data.worlds.new('Aimonite preview world')
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.26,.30,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=2.65
target=Vector((0,0,1.13))
views={'front':(0,-6,1.30),'angle':(3.2,-6,1.65),'side':(6,0,1.35),
       'back':(0,6,1.30),'back_angle':(-3.5,6,1.80)}
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(views)
for name in requested:
    camera.location=views[name]
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(repo/'blender/previews'/('aimonite_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
print('AIMONITE_PREVIEWS',requested)
