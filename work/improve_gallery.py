import bpy, math, os
from mathutils import Vector

ROOT=r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp'
REF=r'C:\Users\takas\.codex\attachments\0ca8192d-80d5-4298-b360-e506eed0f819'
WORK=os.path.join(ROOT,'work')
scene=bpy.context.scene

def color(name, rgb):
    m=bpy.data.materials[name]; m.diffuse_color=(*rgb,1)
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*rgb,1)
    return m

floor=color('床 | 暗いカーペット',(0.025,0.028,0.031))
dark=color('台座 | チャコール',(0.022,0.025,0.028))
black=bpy.data.materials['フレーム | 黒']; paper=bpy.data.materials['資料 | アイボリー']
wall=bpy.data.materials['壁 | 温かみのある白']
wood=bpy.data.materials.get('展示什器 | 濃色木')
if wood is None:
    wood=bpy.data.materials.new('展示什器 | 濃色木'); wood.diffuse_color=(0.17,0.105,0.065,1)
    wood.use_nodes=True; wood.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(0.17,0.105,0.065,1)
lamp=bpy.data.materials['照明パネル']
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0.16
scene.view_settings.exposure=-0.35
for obj in scene.objects:
    if obj.type=='LIGHT' and obj.data.type=='AREA': obj.data.energy *= 0.72

# Subtle carpet texture, visible at human eye level without a repeating image.
n=floor.node_tree.nodes; l=floor.node_tree.links
noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=210; noise.inputs['Detail'].default_value=2
bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=0.16; bump.inputs['Distance'].default_value=0.012
l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])

def cube(name,loc,dims,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material); return o

def image_material(number):
    image=bpy.data.images.load(os.path.join(REF,f'image-{number}.png'),check_existing=True); image.pack()
    m=bpy.data.materials.new(f'参考写真 {number:02d} | 追加'); m.use_nodes=True; n=m.node_tree.nodes
    t=n.new('ShaderNodeTexImage'); t.image=image; p=n.get('Principled BSDF')
    m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']); m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value=0.18; p.inputs['Roughness'].default_value=0.85
    return m,image.size[0]/image.size[1]

def end_photo(number):
    x,y,z=11.94,0,2.02; w,h=5.5,1.95; m,ratio=image_material(number)
    cube('終点 | 地域資料展示フレーム',(x,y,z),(0.10,w+0.14,h+0.14),black)
    cube('終点 | 展示台紙',(x-0.06,y,z),(0.02,w,h),paper)
    pw=min(w-0.14,(h-0.12)*ratio); ph=pw/ratio
    bpy.ops.mesh.primitive_plane_add(size=2,location=(x-0.076,y,z),rotation=(math.pi/2,0,-math.pi/2))
    o=bpy.context.object; o.name='終点 | 参考写真'; o.scale=(pw/2,ph/2,1); o.data.materials.append(m)

def south_photo(number,x,w):
    y,z=-4.93,2.05; h=1.55; m,ratio=image_material(number)
    cube('南壁 | 展示フレーム',(x,y,z),(w+0.12,0.10,h+0.12),black)
    cube('南壁 | 展示台紙',(x,y+0.06,z),(w,0.02,h),paper)
    pw=min(w-0.12,(h-0.12)*ratio); ph=pw/ratio
    bpy.ops.mesh.primitive_plane_add(size=2,location=(x,y+0.076,z),rotation=(-math.pi/2,0,0))
    o=bpy.context.object; o.name='南壁 | 参考写真'; o.scale=(pw/2,ph/2,1); o.data.materials.append(m)

end_photo(9)
south_photo(7,-6.1,2.6)
south_photo(13,8.0,3.0)

# A bench occupies the edge of the gallery, leaving the center route clear.
cube('アート | 見学ベンチ',(0,-2.0,0.46),(2.2,0.56,0.12),wood)
for x in (-0.86,0.86):
    for y in (-2.19,-1.81): cube('ベンチ | 脚',(x,y,0.22),(0.09,0.09,0.44),black)

for x in (-9.4,-6.3,-2.5,0,2.5,6.3,9.6):
    d=bpy.data.lights.new('壁面スポット','SPOT'); d.energy=150; d.spot_size=math.radians(63); d.spot_blend=0.65; d.color=(1.0,0.87,0.71)
    o=bpy.data.objects.new('壁面スポット',d); scene.collection.objects.link(o); o.location=(x,3.35,3.18)
    o.rotation_euler=(Vector((x,4.8,1.9))-o.location).to_track_quat('-Z','Y').to_euler()

scene.render.engine='BLENDER_EEVEE'
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'): scene.eevee.taa_render_samples=32
scene.render.resolution_x=960; scene.render.resolution_y=600; scene.render.resolution_percentage=100
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'museum_revision.blend'))

camera=bpy.data.objects.new('一時プレビュー',bpy.data.cameras.new('一時プレビュー'))
scene.collection.objects.link(camera); camera.data.lens=22; camera.location=(-10.8,-1.5,1.65)
camera.rotation_euler=(Vector((-5.8,1.2,1.55))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera=camera; scene.render.image_settings.file_format='PNG'; scene.render.filepath=os.path.join(WORK,'revision-preview.png')
bpy.ops.render.render(write_still=True)
print('REVISION_PREVIEW_COMPLETE')
