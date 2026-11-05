import bpy, math, os, json
from mathutils import Vector

ROOT=r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp'
WORK=os.path.join(ROOT,'work'); OUT=os.path.join(ROOT,'outputs')
REF=r'C:\Users\takas\.codex\attachments\0ca8192d-80d5-4298-b360-e506eed0f819'
scene=bpy.context.scene
black=bpy.data.materials['フレーム | 黒']; paper=bpy.data.materials['資料 | アイボリー']
light=bpy.data.materials['照明パネル']

def cube(name,loc,dims,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material); return o

def material(name, color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=0.75
    return m

for name in ('終点 | 地域資料展示フレーム','終点 | 展示台紙','終点 | 参考写真'):
    o=bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o,do_unlink=True)

# A wall-length archive case holds three individual scroll details from the supplied reference image.
cube('資料 | 終点ケースの枠',(11.93,0,2.04),(0.12,5.8,2.08),black)
cube('資料 | 終点ケースの背景',(11.85,0,2.04),(0.02,5.57,1.84),paper)
cube('資料 | 終点ケースの照明',(11.79,0,2.90),(0.04,5.40,0.06),light)
cube('資料 | 終点ケースの棚',(11.75,0,1.17),(0.25,5.6,0.07),paper)
img=bpy.data.images.load(os.path.join(REF,'image-12.png'),check_existing=True); img.pack()
for i,(l,t,r,b) in enumerate([(0.31,0.14,0.375,0.56),(0.39,0.17,0.46,0.55),(0.48,0.18,0.54,0.55)]):
    m=bpy.data.materials.new(f'掛軸参考画像 {i+1}'); m.use_nodes=True; n=m.node_tree.nodes; p=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexImage'); tex.image=img; uv=n.new('ShaderNodeTexCoord'); mapping=n.new('ShaderNodeMapping')
    mapping.inputs['Location'].default_value=(l,1-b,0); mapping.inputs['Scale'].default_value=(r-l,b-t,1)
    m.node_tree.links.new(uv.outputs['UV'],mapping.inputs['Vector']); m.node_tree.links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
    m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']); p.inputs['Roughness'].default_value=0.85
    y=1.55-i*1.55; ratio=((r-l)*img.size[0])/((b-t)*img.size[1]); h=1.40; w=h*ratio
    bpy.ops.mesh.primitive_plane_add(size=2,location=(11.83,y,2.02),rotation=(math.pi/2,0,-math.pi/2))
    o=bpy.context.object; o.name=f'資料 | 掛軸の参考画像 {i+1}'; o.scale=(w/2,h/2,1); o.data.materials.append(m)

# Three-dimensional specimen silhouettes on the natural-history study table.
o=bpy.data.objects.get('自然史 | 標本閲覧台 | 写真資料')
if o: bpy.data.objects.remove(o,do_unlink=True)
wing_mats=[material('標本 | 深青',(0.045,0.19,0.37)),material('標本 | 琥珀',(0.65,0.36,0.08)),material('標本 | 淡黄',(0.72,0.65,0.32)),material('標本 | 茶',(0.29,0.16,0.10))]
for row in range(3):
    for col in range(6):
        x=-8.95+col*0.62; y=2.27+row*0.42; z=1.035
        cube('標本 | 胴体',(x,y,z+0.007),(0.025,0.18,0.016),black)
        for side in (-1,1):
            verts=[(x+side*0.02,y,z),(x+side*0.21,y+0.13,z+0.01),(x+side*0.24,y-0.01,z+0.006),(x+side*0.12,y-0.12,z)]
            mesh=bpy.data.meshes.new('標本の翅'); mesh.from_pydata(verts,[],[(0,1,2,3)]); mesh.update()
            ob=bpy.data.objects.new('自然史 | 昆虫標本の模型',mesh); scene.collection.objects.link(ob); ob.data.materials.append(wing_mats[(col+row)%len(wing_mats)])

# The archive tables contain separate paper facsimile objects, with unlettered lines as placeholders.
for name in ('資料 | 閲覧台 A | 写真資料','資料 | 閲覧台 B | 写真資料'):
    o=bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o,do_unlink=True)
for center_x in (6.35,9.65):
    for row in range(2):
        for col in range(4):
            x=center_x-0.88+col*0.58; y=2.43+row*0.52
            cube('資料 | 書類の模型',(x,y,1.033),(0.43,0.35,0.012),paper)
            for j in range(3): cube('資料 | 文字の代替線',(x,y-0.09+j*0.07,1.041),(0.29,0.012,0.002),black)

scene.camera=bpy.data.objects['ウォークスルー カメラ']; scene.frame_set(1)
scene.render.image_settings.file_format='PNG'; scene.render.resolution_x=960; scene.render.resolution_y=600
scene.render.resolution_percentage=100; bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
final=os.path.join(OUT,'museum_walkthrough.blend')
bpy.ops.wm.save_as_mainfile(filepath=final)

camera=bpy.data.objects.new('一時プレビュー',bpy.data.cameras.new('一時プレビュー'))
scene.collection.objects.link(camera); camera.data.lens=22
views=[('01_自然史展示室.png',(-10.8,-1.5,1.65),(-5.8,1.2,1.55)),
       ('02_アート展示室.png',(-3.2,-0.5,1.65),(2.0,1.8,1.55)),
       ('03_資料展示室.png',(5.0,-0.6,1.65),(10.0,2.0,1.55))]
for filename,loc,target in views:
    camera.location=loc; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler(); scene.camera=camera
    scene.render.filepath=os.path.join(OUT,filename); bpy.ops.render.render(write_still=True)
ceiling=bpy.data.collections['天井・照明レール']; ceiling.hide_render=True
camera.data.type='ORTHO'; camera.data.ortho_scale=26.5; camera.location=(0,0,28); camera.rotation_euler=(0,0,0)
scene.render.filepath=os.path.join(OUT,'04_展示室平面.png'); bpy.ops.render.render(write_still=True)
ceiling.hide_render=False; bpy.data.objects.remove(camera,do_unlink=True)

# Low-resolution frames document the actual animated camera path for inspection.
scene.camera=bpy.data.objects['ウォークスルー カメラ']; scene.render.resolution_x=480; scene.render.resolution_y=300
for frame in (1,100,180,260,350,450,540,640,740,840):
    scene.frame_set(frame); scene.render.filepath=os.path.join(WORK,f'walk-{frame:04d}.png'); bpy.ops.render.render(write_still=True)
scene.render.resolution_x=960; scene.render.resolution_y=600; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=final)
print('FINAL_GALLERY_COMPLETE',final)
