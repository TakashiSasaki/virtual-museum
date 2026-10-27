import bpy
import json
import sys
from pathlib import Path

mode = sys.argv[sys.argv.index('--') + 1]
if mode == 'modify-copy':
    coll = bpy.data.collections['展示ケース_標準']
    obj = sorted(coll.objects, key=lambda o: o.name)[0]
    obj.location.x += 0.25
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print('MODIFIED_COPY', obj.name, obj.location.x)
else:
    assert mode == 'inspect'
    assert len(bpy.data.libraries) == 2
    for lib in bpy.data.libraries:
        assert lib.filepath.startswith('//'), lib.filepath
        assert Path(bpy.path.abspath(lib.filepath)).is_file(), lib.filepath
    instances = [o for o in bpy.context.scene.objects if o.instance_type == 'COLLECTION']
    assert len(instances) == 15
    assert all(o.instance_collection and o.instance_collection.library for o in instances)
    coll = next(o.instance_collection for o in instances if o.name.startswith('展示ケース_標準'))
    obj = sorted(coll.objects, key=lambda o: o.name)[0]
    images = [i for i in bpy.data.images if i.users and i.source == 'FILE']
    assert all(i.packed_file or Path(bpy.path.abspath(i.filepath, library=i.library)).exists() for i in images)
    assert bpy.context.scene.camera and bpy.context.scene.frame_end == 840
    print('LINK_CHECK_JSON=' + json.dumps({'libraries': [l.filepath for l in bpy.data.libraries],
                                          'instances': len(instances), 'images': len(images),
                                          'case_object': obj.name, 'case_x': obj.location.x,
                                          'camera': bpy.context.scene.camera.name}, ensure_ascii=True))
