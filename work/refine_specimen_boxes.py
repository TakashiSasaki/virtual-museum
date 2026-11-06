"""Refine the existing specimen boxes; preserve all other workshop assets.

Run in a saved museum_v1_assets.blend. Repeated runs replace only this script's
details, keep the existing drawer names, and export only SpecimenShelf.fbx.
"""
from pathlib import Path
import math
import runpy
import bpy

path = Path(bpy.data.filepath)
if path.name != 'museum_v1_assets.blend' or bpy.data.is_dirty:
    raise RuntimeError('Open the saved V1 workshop before refining boxes')
root = path.resolve().parents[2]
shelf = bpy.data.objects.get('SpecimenShelf')
if not shelf:
    raise RuntimeError('SpecimenShelf source is missing')
prefix = 'Box detail | '
for obj in list(shelf.children):
    if obj.name.startswith(prefix):
        bpy.data.objects.remove(obj, do_unlink=True)

def material(name, color, roughness, metallic=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return m

seam = material('Box detail | Recessed wood join', (.022, .012, .006), .85)
metal = material('Box detail | Aged brass fittings', (.24, .15, .065), .37, .72)
ink = material('Box detail | Label ink', (.045, .038, .028), .85)

def box(name, loc, size, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = prefix + name
    o.parent = shelf
    o.location = loc
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new('Machined edge', 'BEVEL')
        mod.width, mod.segments = bevel, 2
        o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return o

drawers = sorted([o for o in shelf.children if o.name.startswith('Specimen drawer')], key=lambda o: (o.location.z, o.location.x))
if len(drawers) != 14:
    raise RuntimeError('Expected 14 existing specimen boxes')
for index, drawer in enumerate(drawers):
    x, y, z = drawer.location
    # A flat wooden lid has a tighter edge than the original rounded block.
    for modifier in drawer.modifiers:
        if modifier.type == 'BEVEL':
            modifier.width, modifier.segments = .0025, 3
    lid_z = z + .025
    box(f'{index:02d} lid front seam', (x, y-.3605, lid_z), (.844, .001, .0018), seam)
    for side in (-1, 1):
        box(f'{index:02d} lid side seam {side}', (x+side*.4253, y, lid_z), (.001, .715, .0018), seam)
        # Small hinge leaves on the back and two screw heads at each pull.
        box(f'{index:02d} hinge {side}', (x+side*.24, y+.361, lid_z), (.038, .003, .034), metal, .001)
        sx = x + .2 + side*.049
        box(f'{index:02d} pull mounting plate {side}', (sx, y-.365, z), (.019, .007, .026), metal, .002)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6)
        screw=bpy.context.object
        screw.name=prefix+f'{index:02d} pull screw {side}'
        screw.parent=shelf
        screw.location=(sx, y-.370, z)
        screw.scale=(.003, .0015, .003)
        screw.data.materials.append(metal)
    font=bpy.data.curves.new(prefix+f'{index:02d} catalogue text','FONT')
    font.body=str(2601+index*17)
    font.size=.025
    font.align_x='CENTER'
    font.align_y='CENTER'
    font.extrude=.00005
    label=bpy.data.objects.new(prefix+f'{index:02d} catalogue number',font)
    bpy.context.scene.collection.objects.link(label)
    label.parent=shelf
    label.location=(x-.2,y-.3715,z)
    label.rotation_euler=(math.pi/2,0,0)
    label.data.materials.append(ink)
    bpy.ops.object.select_all(action='DESELECT')
    label.select_set(True)
    bpy.context.view_layer.objects.active=label
    bpy.ops.object.convert(target='MESH')

# Preserve the established FBX root: original meshes are direct children of the
# imported model, so the Blender workshop display empty is not exported.
display = shelf.location.copy()
try:
    shelf.location=(0,0,0)
    bpy.context.view_layer.update()
    parts=[obj for obj in shelf.children_recursive if obj.type == 'MESH']
    details=[obj for obj in parts if obj.name.startswith(prefix)]
    export=runpy.run_path(str(root/'work/export_static_fbx.py'))['export_selected_groups']
    export(root/'unity/VirtualMuseum/Assets/Museum/Models/SpecimenShelf.fbx',
           details, passthrough=[obj for obj in parts if obj not in details])
finally:
    shelf.location=display
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print({'boxes':len(drawers),'detail_objects':len([o for o in shelf.children if o.name.startswith(prefix)])})
