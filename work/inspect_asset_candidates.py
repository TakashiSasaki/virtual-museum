import bpy, json

scene = bpy.context.scene
objects = []
for obj in scene.objects:
    if obj.type == 'MESH':
        objects.append({'name': obj.name, 'location': [round(v, 3) for v in obj.location],
                        'parent': obj.parent.name if obj.parent else None,
                        'materials': [m.name if m else None for m in obj.data.materials]})
print('INSPECTION_JSON=' + json.dumps({'objects': objects, 'collections': [c.name for c in bpy.data.collections],
                                      'libraries': [l.filepath for l in bpy.data.libraries],
                                      'packed_images': sum(bool(i.packed_file) for i in bpy.data.images)}, ensure_ascii=True))
