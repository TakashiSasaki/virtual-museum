"""Add three laboratory storage assets to the saved V1 asset workshop.

Run with Blender --background blender/scenes/museum_v1_assets.blend --python.
Only roots tagged by this script may be regenerated. Other assets stay intact.
All models use metres, Z up, front -Y, and a floor-centred origin. Editable
parts remain in the blend; FBX copies are grouped by material for Unity.
"""
import json
import math
import runpy
from pathlib import Path

import bpy
from mathutils import Vector


source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend' or not source.is_file() or bpy.data.is_dirty:
    raise RuntimeError('Open the saved, unmodified V1 asset workshop')
repo = source.resolve().parents[2]
if source.resolve() != repo / 'blender/scenes/museum_v1_assets.blend':
    raise RuntimeError('Unexpected source path')
scene = bpy.data.scenes.get('Museum V1 | Asset workshop')
if scene is None:
    raise RuntimeError('V1 asset workshop scene is missing')
bpy.context.window.scene = scene
destination = repo / 'unity/VirtualMuseum/Assets/Museum/Models'
if not destination.is_dir():
    raise RuntimeError('Unity model directory is missing')
export_groups = runpy.run_path(str(repo / 'work/export_static_fbx.py'))['export_selected_groups']
owner = 'build_lab_storage_v1'
names = ('LabDrawerCabinet', 'LabUtilityCart', 'LabTallCabinet')
owned = set()
for name in names:
    old = bpy.data.objects.get(name)
    if old:
        if old.get('asset_generator') != owner or old.type != 'EMPTY':
            raise RuntimeError('Existing root is not owned by this script: ' + name)
        owned.update([old, *old.children_recursive])
    elif (destination / (name + '.fbx')).exists():
        raise RuntimeError('Existing FBX has no matching generated root: ' + name)


def matrix_values(obj):
    return tuple(tuple(row) for row in obj.matrix_world)


preserved = {o.name: (o.as_pointer(), matrix_values(o), o.data.as_pointer() if o.data else 0)
             for o in bpy.data.objects if o not in owned}
for old in list(owned):
    if old.name in bpy.data.objects:
        bpy.data.objects.remove(old, do_unlink=True)


def material(label, color, roughness, metallic=0):
    name = 'Lab | ' + label
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.roughness, m.metallic = roughness, metallic
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return m


paint = material('Powder coat', (.72, .75, .72), .42)
polymer = material('Black polymer', (.025, .030, .033), .55)
steel = material('Brushed steel', (.48, .52, .54), .27, .85)
rubber = material('Rubber tyres', (.014, .017, .019), .82)
laminate = material('Worktop laminate', (.82, .83, .80), .36)
paper = material('Label paper', (.82, .81, .72), .8)
current_root = None
parts = []
reports = []


def begin(name):
    global current_root, parts
    current_root = bpy.data.objects.new(name, None)
    scene.collection.objects.link(current_root)
    current_root['asset_generator'] = owner
    parts = []


def finish(obj, name, mat, smooth=False):
    obj.name = current_root.name + ' | ' + name
    obj.parent = current_root
    obj.data.materials.append(mat)
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    parts.append(obj)
    return obj


def bevel(obj, radius, segments=3):
    if radius:
        mod = obj.modifiers.new('Manufactured edge', 'BEVEL')
        mod.width, mod.segments = radius, segments
        obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return obj


def box(name, center, size, mat=paint, radius=.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(obj, name, mat)
    return bevel(obj, radius)


def rod(name, a, b, radius, mat=steel, vertices=24, edge=.0008):
    a, b = Vector(a), Vector(b)
    vector = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
        depth=vector.length, location=(a+b)/2)
    obj = bpy.context.object
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = vector.to_track_quat('Z', 'Y')
    finish(obj, name, mat, True)
    return bevel(obj, edge, 2)


def label(name, x, y, z, width, height, text):
    box(name + ' metal holder', (x, y, z), (width+.009, .003, height+.009), steel, .001)
    box(name + ' paper', (x, y-.002, z), (width, .001, height), paper, .0005)
    font = bpy.data.curves.new(current_root.name + ' ' + name + ' type', 'FONT')
    font.body = text
    font.align_x, font.align_y = 'CENTER', 'CENTER'
    font.size = height * .48
    font.extrude = .00003
    obj = bpy.data.objects.new(current_root.name + ' ' + name, font)
    scene.collection.objects.link(obj)
    obj.location = (x, y-.0027, z)
    obj.rotation_euler = (math.pi/2, 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    finish(bpy.context.object, name + ' lettering', polymer)


def pull(name, x, y, z, width=.13, vertical=False):
    if vertical:
        for end in (-1, 1):
            rod(name + ' standoff', (x, y+.015, z+end*width/2),
                (x, y, z+end*width/2), .006)
        rod(name, (x, y, z-width/2), (x, y, z+width/2), .007)
    else:
        for end in (-1, 1):
            rod(name + ' standoff', (x+end*width/2, y+.015, z),
                (x+end*width/2, y, z), .0055)
        rod(name, (x-width/2, y, z), (x+width/2, y, z), .007)


def lock(name, x, y, z):
    rod(name + ' key cylinder', (x, y+.002, z), (x, y-.001, z), .009, steel)
    box(name + ' key slot', (x, y-.0018, z), (.0018, .0008, .008), polymer, .0003)


def levelling_foot(name, x, y, top=.078, radius=.021):
    rod(name + ' threaded stud', (x, y, .014), (x, y, top), .0085, steel)
    rod(name + ' rubber pad', (x, y, .006), (x, y, .019), radius, rubber, edge=.003)
    # Let the rounded lower pad touch Z=0 after its bevel.
    rod(name + ' pad sole', (x, y, 0), (x, y, .010), radius*.91, rubber, edge=.001)


def caster(name, x, y):
    rod(name + ' swivel pin', (x, y, .074), (x, y, .127), .009)
    rod(name + ' swivel race', (x, y, .078), (x, y, .086), .025)
    box(name + ' fork top', (x, y-.006, .074), (.057, .036, .010), steel, .003)
    for side in (-1, 1):
        box(name + ' fork cheek', (x+side*.025, y-.011, .053), (.006, .033, .041), steel, .004)
        wheel_x = x+side*.012
        rod(name + ' rubber wheel', (wheel_x-.009, y-.014, .034),
            (wheel_x+.009, y-.014, .034), .034, rubber, 32, .003)
        rod(name + ' wheel hub', (x+side*.026, y-.014, .034),
            (x+side*.030, y-.014, .034), .013, polymer, 20, .0015)
    rod(name + ' axle', (x-.032, y-.014, .034), (x+.032, y-.014, .034), .004)


def complete(display, expected):
    bpy.context.view_layer.update()
    bounds = [obj.matrix_world @ Vector(corner) for obj in parts for corner in obj.bound_box]
    minimum = [min(p[i] for p in bounds) for i in range(3)]
    maximum = [max(p[i] for p in bounds) for i in range(3)]
    size = [maximum[i]-minimum[i] for i in range(3)]
    if any(size[i] > expected[i]+.004 for i in range(3)) or minimum[2] < -.001:
        raise RuntimeError('Asset exceeded intended furniture footprint: '+str((current_root.name, size, minimum)))
    report = export_groups(destination / (current_root.name+'.fbx'), parts)
    current_root['dimensions_m'] = size
    current_root['editable_parts'] = len(parts)
    current_root.location = display
    reports.append({'asset': current_root.name, 'dimensions_m': size, 'export': report})


begin('LabDrawerCabinet')
# Folded-steel carcass with individually inset drawer fronts and a laminated top.
box('carcass', (0, .010, .355), (.448, .468, .614), paint, .007)
box('recess behind drawers', (0, -.226, .354), (.431, .010, .584), polymer, .001)
for index, (z, height) in enumerate(((.173, .224), (.383, .178), (.561, .166)), 1):
    box(f'drawer {index} front', (0, -.229, z), (.424, .018, height), paint, .004)
    pull(f'drawer {index} handle', 0, -.243, z+.027, .132)
    if index == 3:
        label('drawer label', -.118, -.239, z-.033, .086, .023, 'TOOLS')
lock('drawer lock', .170, -.239, .606)
box('worktop edge seam', (0, .005, .653), (.460, .480, .007), polymer, .002)
box('laminated top', (0, .005, .668), (.460, .490, .024), laminate, .006)
box('recessed plinth', (0, .018, .044), (.402, .410, .047), polymer, .003)
for x in (-.177, .177):
    for y in (-.174, .174):
        levelling_foot('adjustable foot', x, y, .055, .018)
complete((10, 0, 0), (.46, .50, .68))

begin('LabUtilityCart')
# Two shallow trays, four posts and a raised rear push handle.
for x in (-.242, .242):
    for y in (-.151, .151):
        caster('castor', x, y)
        rod('vertical corner post', (x, y, .117), (x, y, .693), .0125, steel)
for index, z in enumerate((.159, .669), 1):
    box(f'tray {index} base', (0, 0, z), (.564, .402, .026), paint, .008)
    box(f'tray {index} inset lining', (0, 0, z+.014), (.527, .365, .003), laminate, .004)
    for x in (-.278, .278):
        box(f'tray {index} raised side', (x, 0, z+.029), (.012, .402, .044), paint, .004)
    for y in (-.195, .195):
        box(f'tray {index} raised end', (0, y, z+.029), (.550, .012, .044), paint, .004)
for x in (-.242, .242):
    rod('push handle upright', (x, .183, .670), (x, .183, .787), .012, steel)
rod('push handle crossbar', (-.242, .183, .787), (.242, .183, .787), .012, steel)
rod('push handle grip', (-.161, .183, .787), (.161, .183, .787), .013, polymer)
for x in (-.280, .280):
    for y in (-.185, .185):
        box('corner protector', (x, y, .668), (.020, .032, .029), rubber, .007)
label('cart identification', 0, -.204, .696, .121, .021, 'COLLECTION')
complete((12, 0, 0), (.58, .42, .80))

begin('LabTallCabinet')
box('steel cabinet body', (0, -.004, .968), (1.082, .418, 1.728), paint, .006)
box('door shadow recess', (0, -.217, .960), (1.050, .008, 1.679), polymer, .001)
box('top folded rim', (0, -.009, 1.835), (1.100, .430, .030), paint, .006)
box('recessed toe plinth', (0, .018, .095), (1.014, .389, .084), polymer, .002)
for side in (-1, 1):
    x = side*.264
    box('left door' if side < 0 else 'right door', (x, -.221, .968),
        (.516, .018, 1.666), paint, .004)
    pull('vertical door pull', side*.052, -.242, 1.019, .180, True)
    for z in (.360, 1.572):
        rod('door hinge barrel', (side*.528, -.225, z-.037),
            (side*.528, -.225, z+.037), .006, steel, edge=.001)
    # Thin horizontal louvers suggest a ventilated laboratory cabinet.
    for i in range(3):
        box('lower ventilation slot', (x, -.2305, .225+i*.025),
            (.236, .0014, .0045), polymer, .001)
lock('cabinet lock', .092, -.231, 1.188)
label('collection holder', -.273, -.232, 1.618, .188, .047, 'COLLECTION')
for x in (-.475, .475):
    for y in (-.165, .165):
        levelling_foot('levelling foot', x, y, .120, .026)
complete((14, 0, 0), (1.10, .46, 1.85))

bpy.context.view_layer.update()
for name, (pointer, transform, data_pointer) in preserved.items():
    obj = bpy.data.objects.get(name)
    if obj is None or obj.as_pointer() != pointer or matrix_values(obj) != transform or (obj.data.as_pointer() if obj.data else 0) != data_pointer:
        raise RuntimeError('Unrelated asset changed: '+name)
bpy.ops.wm.save_as_mainfile(filepath=str(source))
print('LAB_STORAGE', json.dumps({'assets': reports, 'preserved_objects': len(preserved)}))
