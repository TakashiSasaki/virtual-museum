import bpy, math, os
from mathutils import Vector

ROOT = r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp'
OUT = os.path.join(ROOT, 'outputs')
REF = r'C:\Users\takas\.codex\attachments\0ca8192d-80d5-4298-b360-e506eed0f819'
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)

scene = bpy.context.scene
scene.name = '愛媛大学ミュージアム_展示室構想'
bpy.context.preferences.filepaths.save_version = 0
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 5
scene.render.resolution_x = 1120
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.world.color = (0.10, 0.10, 0.10)
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (0.24, 0.26, 0.30, 1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0.32

def mat(name, color, rough=0.55, metallic=0.0, emission=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Alpha'].default_value = alpha
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
    return m

wall = mat('壁 | 温かみのある白', (0.76, 0.745, 0.70), 0.9)
wallwhite = mat('展示壁 | 白', (0.88, 0.86, 0.80), 0.85)
floor = mat('床 | 暗いカーペット', (0.075, 0.080, 0.083), 0.92)
black = mat('フレーム | 黒', (0.028, 0.032, 0.035), 0.46, 0.2)
charcoal = mat('台座 | チャコール', (0.055, 0.060, 0.064), 0.78)
wood = mat('展示什器 | 濃色木', (0.17, 0.105, 0.065), 0.58)
cream = mat('展示台 | 生成り', (0.80, 0.78, 0.70), 0.78)
paper = mat('資料 | アイボリー', (0.90, 0.86, 0.73), 0.9)
clay = mat('資料模型 | 焼き物', (0.46, 0.30, 0.18), 0.8)
clay2 = mat('資料模型 | 淡色陶器', (0.66, 0.58, 0.43), 0.84)
bronze = mat('抽象彫刻 | ブロンズ', (0.30, 0.22, 0.13), 0.35, 0.55)
ivory = mat('抽象彫刻 | 明色', (0.73, 0.70, 0.62), 0.7)
teal = mat('案内色 | 深緑', (0.06, 0.24, 0.20), 0.6)
purple = mat('映像展示 | 紫', (0.23, 0.055, 0.55), 0.3, emission=0.5)
marker = mat('床の動線サイン', (0.18, 0.62, 0.37), 0.6, emission=0.12)
lightmat = mat('照明パネル', (0.96, 0.91, 0.78), 0.4, emission=2.5)
ink = mat('文字 | 炭色', (0.08, 0.09, 0.08), 0.8)
glass = mat('ガラス | 薄い反射', (0.68, 0.80, 0.80), 0.1, alpha=0.075)

def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material: o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new('柔らかな面取り', 'BEVEL'); mod.width = bevel; mod.segments = 2
        o.modifiers.new('法線補正', 'WEIGHTED_NORMAL')
    return o

def cyl(name, loc, radius, depth, material, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def uv_sphere(name, loc, scale, material, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(material)
    bpy.ops.object.shade_smooth(); return o

def point_at(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def area(name, loc, target, power, size, size_y=None, color=(1.0,0.88,0.73)):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.color = color
    if size_y is None: d.shape='DISK'; d.size=size
    else: d.shape='RECTANGLE'; d.size=size; d.size_y=size_y
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; point_at(o, target)
    return o

font = None
try: font = bpy.data.fonts.load(r'C:\Windows\Fonts\BIZ-UDGothicR.ttc')
except Exception: pass

def text_wall(name, body, loc, size, material=ink, align='CENTER'):
    curve = bpy.data.curves.new(name, 'FONT'); curve.body=body; curve.size=size; curve.align_x=align
    if font: curve.font=font
    ob=bpy.data.objects.new(name,curve); scene.collection.objects.link(ob); ob.location=loc
    ob.rotation_euler=(math.pi/2,0,0); curve.materials.append(material)
    return ob

photos = {}
def photo_material(number):
    if number in photos: return photos[number]
    img = bpy.data.images.load(os.path.join(REF, f'image-{number}.png'), check_existing=True)
    img.pack()
    m=bpy.data.materials.new(f'参考写真 {number:02d}'); m.use_nodes=True
    nodes=m.node_tree.nodes; p=nodes.get('Principled BSDF'); tex=nodes.new('ShaderNodeTexImage'); tex.image=img
    m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    m.node_tree.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value=0.14
    p.inputs['Roughness'].default_value=0.83
    photos[number]=(m,img.size[0]/img.size[1]); return photos[number]

def wall_photo(number, x, y, z, width, height, title):
    m, ratio=photo_material(number)
    # Matte backing provides a consistent frame and prevents stretching.
    cube(f'額縁 {title}', (x,y+0.02,z), (width+0.12,0.12,height+0.12), black, 0.015)
    cube(f'台紙 {title}', (x,y-0.045,z), (width,0.018,height), paper)
    w=min(width-0.10,(height-0.10)*ratio); h=w/ratio
    bpy.ops.mesh.primitive_plane_add(size=2, location=(x,y-0.060,z), rotation=(math.pi/2,0,0))
    o=bpy.context.object; o.name=f'展示画像 | {title}'; o.scale=(w/2,h/2,1); o.data.materials.append(m)
    return o

def wall_title(body, x, y, z, width=5.8):
    cube('展示ゾーン名プレート', (x,y,z), (width,0.05,0.34), charcoal, 0.012)
    text_wall('展示ゾーン名', body, (x,y-0.032,z-0.09), 0.19, lightmat)

def glass_vitrine(name, x,y, w,d, base_h=0.75, top=2.42):
    cube(name+' | 台座',(x,y,base_h/2),(w,d,base_h),charcoal,0.025)
    cube(name+' | 中敷',(x,y,base_h+0.035),(w-0.08,d-0.08,0.07),cream)
    zmid=(base_h+top)/2; height=top-base_h
    for xx in (x-w/2+0.018,x+w/2-0.018):
        for yy in (y-d/2+0.018,y+d/2-0.018): cube(name+' | 柱',(xx,yy,zmid),(0.036,0.036,height),black)
    for yy in (y-d/2,y+d/2):
        cube(name+' | 上枠',(x,yy,top),(w,0.04,0.05),black)
        cube(name+' | ガラス',(x,yy,zmid),(w-0.06,0.01,height-0.08),glass)
    for xx in (x-w/2,x+w/2):
        cube(name+' | 上枠',(xx,y,top),(0.04,d,0.05),black)
        cube(name+' | ガラス',(xx,y,zmid),(0.01,d-0.06,height-0.08),glass)
    cube(name+' | 天板',(x,y,top),(w,d,0.035),black)
    cube(name+' | ケース内照明',(x,y,top-0.03),(w-0.12,d-0.12,0.015),lightmat)
    return base_h+0.08

def table_case(name,x,y,w,d,photo):
    cube(name+' | 本体',(x,y,0.70),(w,d,0.58),charcoal,0.025)
    for xx in (x-w/2+0.10,x+w/2-0.10):
        for yy in (y-d/2+0.10,y+d/2-0.10): cube(name+' | 脚',(xx,yy,0.22),(0.10,0.10,0.44),black)
    cube(name+' | 展示面',(x,y,1.005),(w-0.08,d-0.08,0.035),paper)
    m,ratio=photo_material(photo)
    rw=min(w-0.18,(d-0.18)*ratio); rh=rw/ratio
    bpy.ops.mesh.primitive_plane_add(size=2, location=(x,y,1.028))
    o=bpy.context.object; o.name=name+' | 写真資料'; o.scale=(rw/2,rh/2,1); o.data.materials.append(m)
    for yy in (y-d/2,y+d/2): cube(name+' | 縁',(x,yy,1.05),(w,0.045,0.06),black)
    for xx in (x-w/2,x+w/2): cube(name+' | 縁',(xx,y,1.05),(0.045,d,0.06),black)

def vessel(name, x,y,z, height, r, material):
    profile=[(0.04,0),(0.64,0.02),(0.88,0.14),(1.0,0.43),(0.86,0.73),(0.56,0.88),(0.59,1.0),(0.45,1.0),(0.43,0.90)]
    verts=[]; faces=[]; n=32
    for rr,zz in profile:
        for i in range(n):
            a=2*math.pi*i/n; verts.append((x+r*rr*math.cos(a),y+r*rr*math.sin(a),z+height*zz))
    for j in range(len(profile)-1):
        for i in range(n): a=j*n+i; b=j*n+(i+1)%n; faces.append((a,b,b+n,a+n))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); scene.collection.objects.link(ob); ob.data.materials.append(material)
    for f in mesh.polygons: f.use_smooth=True
    return ob

# Architecture: three rooms connected by generous 3.2 m openings.
cube('展示室の床',(0,0,-0.10),(24.2,10.2,0.20),floor)
cube('北側壁',(0,5.08,1.8),(24.2,0.16,3.6),wall)
cube('西側壁',(-12.08,0,1.8),(0.16,10.2,3.6),wall)
cube('東側壁',(12.08,0,1.8),(0.16,10.2,3.6),wall)
# South entrance gap x=-10.4..-8.0.
cube('南壁 西',(-11.25,-5.08,1.8),(1.66,0.16,3.6),wall)
cube('南壁 東',(2.05,-5.08,1.8),(20.10,0.16,3.6),wall)
cube('入口上部',(-9.2,-5.08,3.15),(2.4,0.16,0.9),wall)
for x in (-4,4):
    for y in (-3.3,3.3): cube('展示室間の壁',(x,y,1.8),(0.15,3.4,3.6),wallwhite)
    cube('開口上部',(x,0,3.17),(0.15,3.2,0.86),wallwhite)
    for y in (-1.62,1.62): cube('開口縁',(x,y,1.45),(0.19,0.055,2.9),black)
    cube('開口縁',(x,0,2.90),(0.19,3.24,0.07),black)
for y in (-4.98,4.98): cube('幅木',(0,y,0.08),(24,0.05,0.16),black)

# Keep the ceiling in its own collection so the plan preview can hide it.
ceil=bpy.data.collections.new('天井・照明レール'); scene.collection.children.link(ceil)
def to_ceil(o):
    for col in list(o.users_collection): col.objects.unlink(o)
    ceil.objects.link(o)
to_ceil(cube('黒い天井',(0,0,3.57),(24,10,0.08),black))
for x in range(-12,13): to_ceil(cube('天井格子 X',(x,0,3.44),(0.028,10,0.045),charcoal))
for y in range(-5,6): to_ceil(cube('天井格子 Y',(0,y,3.44),(24,0.028,0.045),charcoal))
for x in (-10,-7,-2,1,6,9):
    for y in (-3.2,3.2):
        to_ceil(cube('天井ライン照明',(x,y,3.40),(1.0,0.12,0.025),lightmat))
        area('展示照明',(x,y,3.28),(x,y*0.62,0.7),260,1.5,1.0)
for x in (-8,0,8): area('室内の拡散光',(x,0,3.30),(x,0,0),420,3.5,3.5,(1.0,0.94,0.85))

# Zone titles and reference-photo panels; the source images are packed into the .blend.
wall_title('自然史  /  NATURAL HISTORY',-8,4.94,3.17,6.3)
wall_title('アートと科学  /  ART & SCIENCE',0,4.94,3.17,6.5)
wall_title('資料と地域  /  ARCHIVES',8,4.94,3.17,6.0)
wall_photo(8,-9.55,4.88,2.06,3.4,1.72,'標本棚の参考写真')
wall_photo(14,-6.25,4.88,2.06,2.6,1.72,'大型標本の参考写真')
wall_photo(2,-2.55,4.88,2.07,2.25,1.65,'美術展示の参考写真')
wall_photo(3,0,4.88,2.07,2.25,1.65,'立体展示の参考写真')
wall_photo(5,2.55,4.88,2.07,2.25,1.65,'照明と空間の参考写真')
wall_photo(12,6.3,4.88,2.07,3.0,1.70,'資料展示の参考写真')
wall_photo(19,9.65,4.88,2.07,3.0,1.70,'地域資料の参考写真')
text_wall('参考写真注記','展示画像は構想用の参考写真です', (0,4.79,0.90),0.14,ink)

# Natural history: two freestanding cases, pottery proxies, and a specimen table.
z=glass_vitrine('自然史 | 標本ケース',-10.3,-2.9,1.55,1.45)
vessel('陶器の模型 A',-10.55,-2.92,z,0.60,0.27,clay)
vessel('陶器の模型 B',-10.0,-2.92,z,0.45,0.21,clay2)
table_case('自然史 | 標本閲覧台',-7.35,2.70,3.7,1.42,8)
z=glass_vitrine('自然史 | 大型標本ケース',-6.6,-2.95,2.6,1.35,0.72,2.1)
uv_sphere('魚類標本をイメージした模型',(-6.7,-2.95,z+0.25),(0.77,0.24,0.23),clay2)
mesh=bpy.data.meshes.new('魚の尾'); mesh.from_pydata([(-5.96,-2.95,z+0.25),(-5.52,-3.15,z+0.45),(-5.52,-2.75,z+0.07)],[],[(0,1,2)])
tail=bpy.data.objects.new('魚類標本 | 尾',mesh); scene.collection.objects.link(tail); tail.data.materials.append(clay2)

# Art/science: plinths, abstract sculpture and suspended geometric panels.
for x in (-2.55,0,2.55): cube('アート | 白い展示台',(x,2.45,0.50),(0.75,0.75,1.0),wallwhite,0.025)
uv_sphere('アート | 球体',(-2.55,2.45,1.34),(0.35,0.35,0.35),bronze)
bpy.ops.mesh.primitive_torus_add(major_radius=0.31,minor_radius=0.10,location=(0,2.45,1.38),rotation=(math.pi/2,0.25,0))
bpy.context.object.name='アート | 環'; bpy.context.object.data.materials.append(ivory)
bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=0.36,radius2=0.09,depth=0.70,location=(2.55,2.45,1.38))
bpy.context.object.name='アート | 立体'; bpy.context.object.data.materials.append(bronze)
for i in range(5):
    x=-2.8+i*1.35
    cube('アート | 吊り下げパネル',(x,-3.10,2.05),(0.55,0.045,2.25),wallwhite)
    for j in range(3):
        p=cube('アート | 幾何模様',(x,-3.135,1.35+j*0.68),(0.34,0.025,0.34),black)
        p.rotation_euler[1]=math.pi/4
cube('映像展示のフレーム',(0,-4.92,1.75),(2.7,0.10,1.6),black)
cube('映像展示の色面',(0,-4.85,1.75),(2.48,0.02,1.38),purple)
text_wall('映像展示タイトル','光と研究のひろば',(0,-4.82,1.70),0.20,lightmat)

# Archive and culture: archival cases and documentary photographs.
table_case('資料 | 閲覧台 A',6.35,2.72,2.6,1.35,7)
table_case('資料 | 閲覧台 B',9.65,2.72,2.6,1.35,11)
for x in (6.5,9.5):
    z=glass_vitrine('資料 | 立体ケース',x,-2.85,2.0,1.4,0.75,2.30)
    for dx in (-0.55,0,0.55): vessel('資料 | 陶器の模型',x+dx,-2.85,z,0.35+0.08*(dx==0),0.18,clay2 if dx==0 else clay)

# Green floor dots mark the intended route; they are low enough to walk over.
for i in range(27):
    x=-10.4+i*0.8
    cyl('床 | 歩行ルート',(x,0,0.008),0.038,0.012,marker,16)

# Walkthrough camera: 35 seconds, eye height, with pauses to inspect each zone.
camdata=bpy.data.cameras.new('ウォークスルー カメラ'); camdata.lens=24; camdata.clip_start=0.05; camdata.clip_end=150
cam=bpy.data.objects.new('ウォークスルー カメラ',camdata); scene.collection.objects.link(cam); scene.camera=cam
waypoints=[
 (1,(-9.2,-3.9,1.62),(-8.7,2.0,1.50)),
 (100,(-8.9,-0.9,1.62),(-9.3,3.8,1.75)),
 (180,(-8.0,0.0,1.62),(-3.7,0.0,1.65)),
 (260,(-4.0,0.0,1.62),(0.2,0.4,1.7)),
 (350,(-1.0,0.0,1.62),(0.0,3.9,1.8)),
 (450,(1.6,0.0,1.62),(5.0,0.0,1.6)),
 (540,(4.0,0.0,1.62),(8.0,0.4,1.6)),
 (640,(7.6,0.0,1.62),(8.5,4.0,1.7)),
 (740,(9.2,0.1,1.62),(9.5,-3.2,1.5)),
 (840,(7.0,0.0,1.62),(3.0,0.0,1.6)),
]
prev=None
for frame, pos, target in waypoints:
    cam.location=pos; rot=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    if prev: rot.make_compatible(prev)
    cam.rotation_euler=rot; prev=rot.copy()
    cam.keyframe_insert(data_path='location',frame=frame); cam.keyframe_insert(data_path='rotation_euler',frame=frame)
# Blender 5 uses layered actions; default smooth interpolation keeps the route continuous.
scene.frame_start=1; scene.frame_end=840; scene.render.fps=24; scene.frame_set(1)

note=bpy.data.texts.new('お読みください | 展示室の操作')
note.write('''愛媛大学ミュージアムの参考写真から構成したバーチャル展示室の設計案です。\n寸法・展示品の形状は構想用の仮設定であり、実際の展示室や資料の正確な再現ではありません。\n\n・カメラ「ウォークスルー カメラ」にはフレーム1〜840（24fps）の見学経路があります。\n・テンキー0でカメラ表示、スペースキーで再生します。タイムラインをドラッグして各展示室へ移動できます。\n・自由に歩くには3Dビューで Shift + `（バッククォート）を押し、W/A/S/Dとマウスで移動します。終了は左クリックまたはEscです。\n・写真はご提供いただいた参考写真をファイルに埋め込んでいます。陶器・魚・彫刻は雰囲気を示す模型です。\n・展示替えや実資料への差し替えは各オブジェクトを選択して行えます。\n''')

for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type == 'VIEW_3D':
            ar.spaces.active.region_3d.view_perspective='CAMERA'

blend_path=os.path.join(OUT,'museum_walkthrough.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Render two representative eye-level views and a roof-off plan view.
preview=bpy.data.objects.new('プレビュー専用カメラ',bpy.data.cameras.new('プレビュー専用カメラ'))
scene.collection.objects.link(preview); preview.data.lens=22; preview.data.clip_start=0.05
for name,loc,target in [
    ('01_自然史展示室.png',(-10.8,-1.5,1.65),(-5.8,1.2,1.55)),
    ('02_アート展示室.png',(-3.2,-0.5,1.65),(2.0,1.8,1.55)),
    ('03_資料展示室.png',(5.0,-0.6,1.65),(10.0,2.0,1.55)),
]:
    preview.location=loc; point_at(preview,target); scene.camera=preview
    scene.render.filepath=os.path.join(OUT,name); bpy.ops.render.render(write_still=True)

ceil.hide_render=True
preview.data.type='ORTHO'; preview.data.ortho_scale=26.5
preview.location=(0,0,28); preview.rotation_euler=(0,0,0)
scene.render.filepath=os.path.join(OUT,'04_展示室平面.png'); bpy.ops.render.render(write_still=True)
ceil.hide_render=False

scene.camera=cam; scene.frame_set(1)
bpy.data.objects.remove(preview,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print('CREATED',blend_path)
