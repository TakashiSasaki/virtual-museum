import bpy, os, math
from mathutils import Vector

ROOT=r'C:\Users\takas\Documents\Codex\2026-10-26\pc-blender-mcp'
WORK=os.path.join(ROOT,'work')
scene=bpy.context.scene

def crop_material(name, bounds):
    m=bpy.data.materials.get(name)
    if not m: raise RuntimeError(f'Material missing: {name}')
    nodes=m.node_tree.nodes; links=m.node_tree.links
    tex=next(n for n in nodes if n.type=='TEX_IMAGE')
    l,t,r,b=bounds
    uv=nodes.new('ShaderNodeTexCoord'); mapping=nodes.new('ShaderNodeMapping')
    mapping.inputs['Location'].default_value=(l,1-b,0)
    mapping.inputs['Scale'].default_value=(r-l,b-t,1)
    links.new(uv.outputs['UV'],mapping.inputs['Vector']); links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
    return ((r-l)*tex.image.size[0])/((b-t)*tex.image.size[1])

def fit(name, ratio, max_w, max_h):
    o=bpy.data.objects.get(name)
    if o is None: raise RuntimeError(f'Object missing: {name}')
    w=min(max_w,max_h*ratio); h=w/ratio
    o.scale.x=w/2; o.scale.y=h/2

specs=[
 ('参考写真 08',(0.37,0.17,0.69,0.49),'展示画像 | 標本棚の参考写真',3.30,1.62),
 ('参考写真 14',(0.25,0.38,1.00,0.79),'展示画像 | 大型標本の参考写真',2.50,1.62),
 ('参考写真 02',(0.29,0.28,0.38,0.57),'展示画像 | 美術展示の参考写真',2.15,1.55),
 ('参考写真 03',(0.56,0.15,0.92,0.88),'展示画像 | 立体展示の参考写真',2.15,1.55),
 ('参考写真 05',(0.15,0.18,0.48,0.87),'展示画像 | 照明と空間の参考写真',2.15,1.55),
 ('参考写真 12',(0.27,0.12,0.71,0.63),'展示画像 | 資料展示の参考写真',2.90,1.60),
 ('参考写真 19',(0.66,0.19,0.94,0.73),'展示画像 | 地域資料の参考写真',2.90,1.60),
 ('参考写真 09 | 追加',(0.04,0.37,0.94,0.82),'終点 | 参考写真',5.36,1.83),
]
for material,bounds,obj,w,h in specs:
    fit(obj,crop_material(material,bounds),w,h)
for name in ('参考写真 07','参考写真 07 | 追加'):
    crop_material(name,(0.14,0.53,0.63,0.99))
crop_material('参考写真 11',(0.41,0.48,0.70,0.76))
crop_material('参考写真 13 | 追加',(0.62,0.17,0.93,0.81))

# The source photograph shows a seal, so represent it as an approximate seal rather than a fish.
body=bpy.data.objects.get('魚類標本をイメージした模型')
if body:
    body.name='海獣標本 | アザラシの模型'; body.scale=(0.78,0.28,0.24)
    body.data.materials.clear(); body.data.materials.append(bpy.data.materials['資料模型 | 焼き物'])
tail=bpy.data.objects.get('魚類標本 | 尾')
if tail: bpy.data.objects.remove(tail,do_unlink=True)
mat=bpy.data.materials['資料模型 | 焼き物']; dark=bpy.data.materials['フレーム | 黒']
def sphere(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o
sphere('アザラシ模型 | 頭',(-7.39,-2.95,1.05),(0.24,0.23,0.20),mat)
sphere('アザラシ模型 | 前脚',(-6.95,-3.14,0.92),(0.33,0.13,0.07),mat)
sphere('アザラシ模型 | 後肢',(-5.99,-2.95,0.96),(0.30,0.25,0.06),mat)
sphere('アザラシ模型 | 目',(-7.51,-3.13,1.12),(0.025,0.025,0.025),dark)

scene.frame_set(1); scene.camera=bpy.data.objects['ウォークスルー カメラ']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK,'museum_final_candidate.blend'))

preview=bpy.data.objects.new('一時プレビュー',bpy.data.cameras.new('一時プレビュー'))
scene.collection.objects.link(preview); preview.data.lens=22
for filename,loc,target in [
 ('natural-refined.png',(-10.8,-1.5,1.65),(-5.8,1.2,1.55)),
 ('archive-refined.png',(5.0,-0.6,1.65),(10.0,2.0,1.55)),
]:
    preview.location=loc; preview.rotation_euler=(Vector(target)-preview.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=preview; scene.render.filepath=os.path.join(WORK,filename); bpy.ops.render.render(write_still=True)
print('REFINED_PREVIEWS_COMPLETE')
