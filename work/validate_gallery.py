import bpy, json, os
from mathutils import Vector

scene=bpy.context.scene
cam=bpy.data.objects.get('ウォークスルー カメラ')
assert cam and scene.camera == cam, 'Walkthrough camera is not active'
assert scene.frame_start == 1 and scene.frame_end == 840 and scene.render.fps == 24
assert cam.animation_data and cam.animation_data.action, 'Camera animation missing'
assert bpy.data.texts.get('お読みください | 展示室の操作'), 'Embedded instructions missing'
assert len([o for o in scene.objects if '昆虫標本の模型' in o.name]) >= 36
assert len([o for o in scene.objects if '掛軸の参考画像' in o.name]) == 3

missing=[im.name for im in bpy.data.images if im.users and im.source=='FILE' and not im.packed_file]
assert not missing, f'Unpacked image assets: {missing}'

prefixes=('展示室間の壁','開口縁','北側壁','南壁','西側壁','東側壁','入口上部',
          '自然史 | 標本ケース | 台座','自然史 | 大型標本ケース | 台座',
          '自然史 | 標本閲覧台 | 本体','資料 | 閲覧台 A | 本体','資料 | 閲覧台 B | 本体',
          '資料 | 立体ケース | 台座','アート | 白い展示台','アート | 見学ベンチ')
obstacles=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(prefixes)]
hits=[]; sampled=[]
for frame in range(1,841,5):
    scene.frame_set(frame); pos=cam.matrix_world.translation.copy(); sampled.append([frame,*map(lambda x:round(x,3),pos)])
    for o in obstacles:
        points=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
        lo=[min(v[i] for v in points) for i in range(3)]; hi=[max(v[i] for v in points) for i in range(3)]
        margin=0.16
        if lo[0]-margin < pos.x < hi[0]+margin and lo[1]-margin < pos.y < hi[1]+margin and lo[2] < pos.z < hi[2]:
            hits.append({'frame':frame,'obstacle':o.name,'position':[round(pos.x,3),round(pos.y,3),round(pos.z,3)]})

report={'camera':cam.name,'frames':[scene.frame_start,scene.frame_end],'fps':scene.render.fps,
        'objects':len(scene.objects),'packed_images':len([im for im in bpy.data.images if im.packed_file]),
        'unpacked_images':missing,'sampled_frames':len(sampled),'collisions':hits,'positions':sampled[::20]}
print(json.dumps(report,ensure_ascii=False))
if hits: raise RuntimeError(f'Camera path intersects {len(hits)} obstacle samples')
