"""Split saved exhibition assets without touching an open Blender session."""
import bpy
import json
from pathlib import Path
from collections import Counter
from mathutils import Vector

ROOT = Path(bpy.data.filepath).resolve().parent.parent
OUT = ROOT / 'outputs'
ASSETS = OUT / 'shared' / 'museum-assets'
ASSETS.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene

def named(prefix):
    return [o for o in scene.objects if o.name.startswith(prefix)]

def world_geometry():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    records = []
    for item in deps.object_instances:
        obj = item.object
        if obj.type != 'MESH':
            continue
        mesh = obj.to_mesh()
        coords = sorted(tuple(round(v, 4) for v in item.matrix_world @ vertex.co) for vertex in mesh.vertices)
        bounds = (coords[0], coords[-1]) if coords else ()
        # Shape moments protect against changes that leave the bounding box intact.
        moments = tuple(round(sum(p[i] for p in coords), 3) for i in range(3))
        material_names = tuple(m.name for m in mesh.materials if m)
        records.append((len(coords), len(mesh.polygons), bounds, moments, material_names))
        obj.to_mesh_clear()
    return Counter(records)

before = world_geometry()

# (library, collection name, representative objects, origin, all originals, instance locations)
groups = []
def group(lib, name, representative, origin, originals=None, positions=None):
    assert representative, name
    assert all(o.parent is None for o in representative), name
    groups.append((lib, name, representative, Vector(origin), originals or representative,
                   positions or [origin]))

group('furniture', '展示ケース_標準', named('自然史 | 標本ケース | '), (-10.3, -2.9, 0))
group('furniture', '展示ケース_大型', named('自然史 | 大型標本ケース | '), (-6.6, -2.95, 0))
archive_cases = named('資料 | 立体ケース | ')
group('furniture', '展示ケース_資料', [o for o in archive_cases if o.location.x < 8], (6.5, -2.85, 0),
      archive_cases, [(6.5, -2.85, 0), (9.5, -2.85, 0)])
group('furniture', '閲覧台_自然史', named('自然史 | 標本閲覧台 | '), (-7.35, 2.7, 0))
archive_a, archive_b = named('資料 | 閲覧台 A | '), named('資料 | 閲覧台 B | ')
group('furniture', '閲覧台_資料', archive_a, (6.35, 2.72, 0), archive_a + archive_b,
      [(6.35, 2.72, 0), (9.65, 2.72, 0)])
pedestals = named('アート | 白い展示台')
group('furniture', '展示台_白', [pedestals[0]], (-2.55, 2.45, 0), pedestals,
      [(-2.55, 2.45, 0), (0, 2.45, 0), (2.55, 2.45, 0)])
group('furniture', '見学ベンチ', [bpy.data.objects['アート | 見学ベンチ']] + named('ベンチ | 脚'), (0, -2, 0))
for label, objname, origin in [
    ('彫刻_球体', 'アート | 球体', (-2.55, 2.45, 0)),
    ('彫刻_環', 'アート | 環', (0, 2.45, 0)),
    ('彫刻_立体', 'アート | 立体', (2.55, 2.45, 0)),
]:
    group('exhibits', label, [bpy.data.objects[objname]], origin)
group('exhibits', '標本模型_アザラシ', [bpy.data.objects['海獣標本 | アザラシの模型']] + named('アザラシ模型 | '), (-6.6, -2.95, 0))

# Keep source objects intact until the replacement geometry has been checked.
temporary = []
for lib, name, representatives, origin, originals, positions in groups:
    coll = bpy.data.collections.new(name)
    coll.asset_mark()
    coll.asset_data.description = '展示室から分離した再利用可能なアセット。原点は床面。'
    temporary.append((lib, coll))
    for original in representatives:
        copy = original.copy()
        copy.matrix_world = original.matrix_world.copy()
        copy.location -= origin
        coll.objects.link(copy)

for lib in ('furniture', 'exhibits'):
    path = ASSETS / (lib + '.blend')
    assert not path.exists(), f'Refusing to overwrite {path}'
    bpy.data.libraries.write(str(path), {c for category, c in temporary if category == lib}, fake_user=True, compress=True)

# Remove temporary source collections and their object copies before loading linked collections.
for _, coll in temporary:
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(coll)

loaded = {}
for lib in ('furniture', 'exhibits'):
    path = ASSETS / (lib + '.blend')
    with bpy.data.libraries.load(str(path), link=True, relative=True) as (available, requested):
        requested.collections = [name for category, name, *_ in groups if category == lib]
    loaded.update({coll.name: coll for coll in requested.collections})

root = bpy.data.collections.new('リンクされた共有アセット')
scene.collection.children.link(root)
for lib, name, representatives, origin, originals, positions in groups:
    for obj in originals:
        bpy.data.objects.remove(obj, do_unlink=True)
    for index, position in enumerate(positions, 1):
        instance = bpy.data.objects.new(f'{name} | 配置 {index:02}', None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = loaded[name]
        instance.location = position
        root.objects.link(instance)

after = world_geometry()
if before != after:
    print('GEOMETRY_MISMATCH', json.dumps({'missing': list((before-after).items())[:5], 'extra': list((after-before).items())[:5]}, ensure_ascii=False))
    raise RuntimeError('Scene geometry changed; refusing to save')

for lib in bpy.data.libraries:
    assert lib.filepath.startswith('//'), lib.filepath
assert len(bpy.data.libraries) == 2
assert scene.camera and scene.frame_end == 840
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'museum_walkthrough_linked.blend'))
print('SPLIT_OK ' + json.dumps({'asset_groups': len(groups), 'instances': sum(len(g[-1]) for g in groups),
                              'mesh_instances': sum(after.values()),
                              'libraries': [lib.filepath for lib in bpy.data.libraries]}, ensure_ascii=False))
