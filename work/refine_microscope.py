"""Replace only the saved V1 workshop's microscope, then export its existing FBX.

Open blender/scenes/museum_v1_assets.blend in a separate Blender process and run
this file using --python. No Unity scene, .meta, other asset or rig is rebuilt.
Front is -Y; the bench surface is Z=0. Dimensions fit the existing interaction
box (0.42 x 0.50 m footprint, 0.65 m height). The reference informs the mechanical
layout; this is an illustrative stereo microscope, not a branded instrument.
"""
import json
import math
from pathlib import Path
import runpy

import bpy
from mathutils import Vector


source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend' or not source.is_file():
    raise RuntimeError('Open the existing V1 asset workshop before refinement')
if bpy.data.is_dirty:
    raise RuntimeError('Save or discard pending Blender edits before refinement')
repo = source.resolve().parents[2]
if source.resolve() != repo / 'blender/scenes/museum_v1_assets.blend':
    raise RuntimeError('Unexpected V1 source location')
destination = repo / 'unity/VirtualMuseum/Assets/Museum/Models/Microscope.fbx'
if not destination.is_file():
    raise RuntimeError('Expected existing Microscope.fbx; refusing a new location')
scene = bpy.data.scenes.get('Museum V1 | Asset workshop')
root = bpy.data.objects.get('Microscope')
if scene is None or root is None or root.type != 'EMPTY' or root.name not in scene.objects:
    raise RuntimeError('Expected the Microscope empty in the V1 workshop scene')
bpy.context.window.scene = scene
old_parts = list(root.children_recursive)
if not old_parts or any(o.type not in {'MESH', 'CURVE', 'FONT', 'EMPTY'} for o in old_parts):
    raise RuntimeError('Unexpected microscope hierarchy; inspect before replacing')
preserved = {o.name: (o.as_pointer(), tuple(o.matrix_world))
             for o in bpy.data.objects if o != root and o not in old_parts}
created = []


def material(label, color, roughness, metallic=0):
    name = 'Microscope | ' + label
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.metallic = metallic
    m.roughness = roughness
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


enamel = material('Warm white enamel', (.81, .83, .80), .29)
housing = material('Optical housing', (.67, .71, .69), .35)
rubber = material('Eyecup rubber', (.018, .021, .023), .71)
anodized = material('Black anodized aluminium', (.027, .035, .040), .30, .65)
metal = material('Brushed steel', (.43, .48, .50), .26, .82)
stage = material('Stage ceramic', (.91, .92, .88), .23)
glass = material('Coated optical glass', (.018, .055, .065), .12, .52)
diffuser = material('LED diffuser', (.80, .88, .88), .20)
marking = material('Scale markings', (.64, .69, .68), .49)
green = material('Camera status light', (.045, .38, .13), .28)


def finish(o, name, mat, smooth=False):
    o.name = 'Scope ' + name
    o.data.materials.append(mat)
    if smooth and o.type == 'MESH':
        for polygon in o.data.polygons:
            polygon.use_smooth = True
    created.append(o)
    return o


def bevel(o, width, segments=3):
    mod = o.modifiers.new('Manufactured edge radii', 'BEVEL')
    mod.width = width
    mod.segments = segments
    o.modifiers.new('Weighted face normals', 'WEIGHTED_NORMAL')
    return o


def box(name, center, dimensions, mat, radius=.004):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object
    o.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(o, name, mat)
    return bevel(o, radius) if radius else o


def barrel(name, start, end, radius, mat, end_radius=None, edge=.001, vertices=40):
    a, b = Vector(start), Vector(end)
    d = b-a
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
        radius2=radius if end_radius is None else end_radius, depth=d.length,
        location=(a+b)/2)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    finish(o, name, mat, True)
    return bevel(o, edge, 2) if edge else o


def ring(name, center, axis, radius, thickness, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=10,
        location=center, major_radius=radius, minor_radius=thickness)
    o = bpy.context.object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector(axis).to_track_quat('Z', 'Y')
    return finish(o, name, mat, True)


def tube(name, controls, radius, mat, corrugations=0, samples=80):
    """Sweep a cubic tube; radius ribs are actual mesh, visible in silhouette."""
    p = [Vector(point) for point in controls]
    sides = 12
    verts, faces = [], []
    for i in range(samples+1):
        t = i/samples
        center = (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
        tangent = (3*(1-t)**2*(p[1]-p[0])+6*(1-t)*t*(p[2]-p[1])
                   +3*t*t*(p[3]-p[2])).normalized()
        reference = Vector((1, 0, 0))
        if abs(tangent.dot(reference)) > .95:
            reference = Vector((0, 1, 0))
        n = tangent.cross(reference).normalized()
        b = tangent.cross(n).normalized()
        r = radius*(1+.12*math.cos(math.tau*corrugations*t)) if corrugations else radius
        for j in range(sides):
            a = j*math.tau/sides
            verts.append(center+r*(math.cos(a)*n+math.sin(a)*b))
        if i:
            for j in range(sides):
                k = i*sides+j
                faces.append((k-sides, i*sides+(j+1)%sides-sides,
                              i*sides+(j+1)%sides, k))
    faces += [tuple(reversed(range(sides))), tuple(samples*sides+j for j in range(sides))]
    mesh = bpy.data.meshes.new('Scope ' + name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new('Scope ' + name, mesh)
    scene.collection.objects.link(o)
    return finish(o, name, mat, True)


def screw(name, center, axis, radius=.003):
    c, d = Vector(center), Vector(axis).normalized()
    barrel(name, c-d*.0008, c+d*.0008, radius, metal, edge=.00035, vertices=16)
    # A thin black slot reads as a recessed screw from normal viewing distance.
    slot = box(name+' slot', c+d*.0009, (radius*1.35, .00055, .00045), rubber, .00015)
    slot.rotation_mode = 'QUATERNION'
    slot.rotation_quaternion = d.to_track_quat('Z', 'Y')


# Cast base: a lower lip, rounded upper casting and four non-slip feet.
for x in (-.119, .119):
    for y in (-.155, .135):
        barrel('Base rubber foot', (x, y, .001), (x, y, .012), .022, rubber)
box('Base lower seam', (0, -.015, .026), (.308, .389, .032), housing, .015)
box('Microscope base', (0, -.015, .045), (.320, .400, .050), enamel, .024)
# The flat circular stage remains open below the objective.
barrel('Stage retaining rim', (0, -.067, .068), (0, -.067, .072), .076, metal)
barrel('Circular stage insert', (0, -.067, .071), (0, -.067, .074), .070, stage)
for x in (-.096, .096):
    barrel('Stage clip pivot', (x, -.031, .069), (x, -.031, .076), .008, metal)
    clip = box('Spring stage clip', (x*.84, -.080, .078), (.012, .102, .0028), metal, .001)
    clip.rotation_euler.z = math.copysign(.25, x)
    screw('Stage clip screw', (x, -.031, .077), (0, 0, 1), .003)

# Tall rear column and focusing carriage; no floating optical head.
box('Column mounting plinth', (0, .111, .089), (.118, .101, .045), enamel, .012)
box('Rear support column', (0, .120, .291), (.064, .071, .392), enamel, .012)
box('Column rear cover', (0, .157, .292), (.047, .005, .335), housing, .003)
box('Focus vertical slide rail', (0, .082, .318), (.034, .007, .292), metal, .002)
box('Focus carriage', (0, .068, .408), (.123, .113, .096), enamel, .011)
box('Head support bridge', (0, .012, .419), (.115, .110, .071), enamel, .012)
for z in (.132, .451):
    screw('Column cover screw', (0, .160, z), (0, 1, 0))
for sign in (-1, 1):
    a = Vector((sign*.061, .077, .405))
    axis = Vector((sign, 0, 0))
    barrel('Focus axle', a, a+axis*.018, .020, metal)
    barrel('Coarse focus wheel', a+axis*.012, a+axis*.041, .034, rubber, edge=.002)
    barrel('Focus wheel inset', a+axis*.041, a+axis*.044, .025, anodized)
    barrel('Fine focus wheel', a+axis*.043, a+axis*.056, .016, rubber)
    barrel('Fine focus cap', a+axis*.056, a+axis*.058, .012, housing)
    # Narrow axial ribs around the coarse wheel add believable rubber grip.
    for k in range(24):
        angle = k*math.tau/24
        offset = Vector((0, .033*math.cos(angle), .033*math.sin(angle)))
        barrel('Focus grip rib', a+axis*.015+offset, a+axis*.038+offset,
               .0013, rubber, edge=0, vertices=8)

# Zoom housing and working-distance objective stack.
barrel('Zoom body', (0, -.033, .359), (0, -.033, .449), .058, enamel,
       end_radius=.066, edge=.006)
barrel('Zoom lower ring', (0, -.033, .341), (0, -.033, .361), .056, rubber)
barrel('Objective collar', (0, -.033, .321), (0, -.033, .341), .047, metal)
barrel('Objective barrel', (0, -.033, .282), (0, -.033, .323), .046, anodized,
       end_radius=.047)
barrel('Objective bottom recess', (0, -.033, .279), (0, -.033, .284), .041, rubber)
barrel('Objective optical glass', (0, -.033, .2785), (0, -.033, .280), .029, glass)
ring('Objective protective lip', (0, -.033, .279), (0, 0, 1), .039, .0023, metal)
for sign in (-1, 1):
    barrel('Zoom adjustment spindle', (sign*.050, -.034, .385),
           (sign*.072, -.034, .385), .014, housing)
    barrel('Zoom adjustment knob', (sign*.071, -.034, .385),
           (sign*.086, -.034, .385), .020, rubber)
    for k in range(10):
        angle = (k/9-.5)*1.9
        x, y = .057*math.sin(angle), -.033-.057*math.cos(angle)
        tick = box('Zoom graduation', (x, y, .352), (.0012, .0013, .005), marking, 0)
        tick.rotation_euler.z = -angle

# Binocular viewing unit. Both eyepieces have separate pupils and recessed glass.
box('Binocular prism housing', (0, -.034, .463), (.139, .115, .073), enamel, .018)
for sign in (-1, 1):
    start = Vector((sign*.036, -.053, .470))
    end = Vector((sign*.058, -.144, .535))
    direction = (end-start).normalized()
    collar = start+(end-start)*.55
    barrel('Angled binocular arm', start, collar, .035, enamel,
           end_radius=.029, edge=.004)
    barrel('Eyepiece diopter barrel', collar, end-direction*.009, .0255, anodized)
    ring('Diopter adjustment ring', end-direction*.020, direction, .0255, .0025, rubber)
    barrel('Rubber eyecup body', end-direction*.012, end+direction*.006,
           .027, rubber, end_radius=.030, edge=.002)
    # Nested concentric surfaces keep the ocular visibly hollow.
    barrel('Eyecup dark well', end+direction*.006, end+direction*.0065, .025, rubber, edge=0)
    barrel('Eyepiece lens', end+direction*.007, end+direction*.0075, .0185, glass, edge=0)
    ring('Soft eyecup rim', end+direction*.009, direction, .0265, .0036, rubber)
    for k in range(10):
        angle = (k/9-.5)*1.8
        offset = Vector((math.sin(angle)*.027, -math.cos(angle)*.027, 0))
        q = direction.to_track_quat('Z', 'Y')
        point = end-direction*.023+q@offset
        barrel('Diopter scale tick', point-direction*.002, point+direction*.002,
               .00055, marking, edge=0, vertices=8)

# Trinocular camera port and camera with controls, mount and tether.
barrel('Camera port white socket', (0, .025, .476), (0, .025, .513), .027, enamel)
barrel('Camera adapter lower tube', (0, .025, .510), (0, .025, .551), .022, anodized)
ring('Camera adapter locking ring', (0, .025, .526), (0, 0, 1), .023, .003, rubber)
barrel('Camera adapter upper tube', (0, .025, .549), (0, .025, .579), .018, anodized)
box('Camera sensor body', (0, .025, .603), (.095, .066, .057), anodized, .007)
box('Camera front panel', (0, -.009, .604), (.081, .004, .039), rubber, .003)
box('Camera rear inset', (0, .060, .605), (.064, .003, .030), rubber, .002)
box('Camera side connector', (.049, .029, .603), (.010, .023, .017), rubber, .002)
for x in (-.029, .029):
    screw('Camera front screw', (x, -.012, .612), (0, -1, 0), .0022)
barrel('Camera status indicator', (.025, -.012, .595), (.025, -.014, .595), .0022, green)
box('Camera top button', (.028, .025, .633), (.017, .018, .004), rubber, .0015)
tube('Camera cable', [(.054, .030, .603), (.128, .092, .611),
                      (.103, .193, .106), (.055, .184, .018)], .0024, rubber, samples=64)

# Two independently posed flexible illuminators on the bench, aimed at the stage.
for sign in (-1, 1):
    x = sign*.167
    box('LED weighted foot', (x, .043, .017), (.082, .113, .032), rubber, .010)
    box('LED control enclosure', (x, .056, .036), (.067, .079, .018), anodized, .005)
    barrel('LED intensity dial', (x, .042, .044), (x, .042, .051), .010, rubber)
    box('LED dial pointer', (x, .038, .052), (.0012, .007, .001), marking, .0003)
    start = (x, .079, .048)
    end = Vector((sign*.148, -.015, .271))
    tube('Ribbed flexible LED neck', [start, (sign*.186, .103, .215),
         (sign*.192, .014, .311), end], .0083, anodized,
         corrugations=38, samples=152)
    direction = (Vector((sign*.024, -.066, .078))-end).normalized()
    barrel('LED swivel joint', end-direction*.006, end+direction*.014, .015, rubber)
    barrel('LED lamp housing', end+direction*.007, end+direction*.055,
           .023, anodized, end_radius=.025, edge=.003)
    for distance in (.019, .027, .035):
        ring('LED cooling fin', end+direction*distance, direction, .024, .0017, anodized)
    barrel('LED inset glass', end+direction*.055, end+direction*.057, .0205, diffuser)
    ring('LED bezel', end+direction*.057, direction, .023, .002, rubber)
    for k in range(6):
        a = k*math.tau/6
        orientation = direction.to_track_quat('Z', 'Y')
        offset = orientation@Vector((math.cos(a)*.012, math.sin(a)*.012, 0))
        barrel('LED lens element', end+direction*.0575+offset,
               end+direction*.058+offset, .0035, stage, edge=0, vertices=12)
    tube('LED power cord', [(x, .106, .021), (x, .153, .012),
         (sign*.117, .180, .009), (sign*.079, .190, .009)], .0023, rubber, samples=24)

# Replace only the old subtree. Keep the empty and all unrelated assets intact.
for old in old_parts:
    bpy.data.objects.remove(old, do_unlink=True)
for obj in created:
    obj.parent = root
root['refinement'] = 'Stereo microscope with binocular optics, camera and dual LED lighting'
root['reference_dimensions_m'] = [.418, .420, .636]
bpy.context.view_layer.update()
for name, (pointer, transform) in preserved.items():
    other = bpy.data.objects.get(name)
    if other is None or other.as_pointer() != pointer or tuple(other.matrix_world) != transform:
        raise RuntimeError('Unrelated asset changed: '+name)

bpy.ops.object.select_all(action='DESELECT')
for obj in created:
    obj.select_set(True)
bpy.context.view_layer.objects.active = created[0]
position = root.location.copy()
try:
    root.location = (0, 0, 0)
    bpy.context.view_layer.update()
    bounds = [obj.matrix_world@Vector(corner) for obj in created for corner in obj.bound_box]
    size = [max(p[i] for p in bounds)-min(p[i] for p in bounds) for i in range(3)]
    if size[0] > .43 or size[1] > .50 or size[2] > .65:
        raise RuntimeError('Refined microscope exceeds existing interaction bounds: '+str(size))
    export_selected_groups = runpy.run_path(str(repo/'work/export_static_fbx.py'))['export_selected_groups']
    export_report = export_selected_groups(destination, created)
finally:
    root.location = position
    bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(source))
print('MICROSCOPE_REFINEMENT', json.dumps({'parts': len(created), 'size_m': size,
    'preserved_objects': len(preserved), 'fbx': destination.name,
    'export': export_report}, ensure_ascii=False))
