"""Add two editable laboratory swivel seats to the saved V1 asset workshop.

Run with the existing museum_v1_assets.blend in a separate Blender process.
Only tagged LabSwivelChair/LabRoundStool assets are replaced on repeat runs.
The static FBX exports group by material; the source retains separate parts.
Units are metres, +Z is up, and the chair faces -Y. No scene layout is changed.
"""
import json
import math
import runpy
from pathlib import Path

import bpy
from mathutils import Vector

source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend' or bpy.data.is_dirty:
    raise RuntimeError('Open the saved V1 asset workshop before adding seats')
repo = source.resolve().parents[2]
if source.resolve() != repo/'blender/scenes/museum_v1_assets.blend':
    raise RuntimeError('Unexpected V1 source path')
scene = bpy.data.scenes.get('Museum V1 | Asset workshop')
if not scene:
    raise RuntimeError('The V1 asset workshop scene is missing')
bpy.context.window.scene = scene
tag = 'museum_lab_seating_v1'
names = ('LabSwivelChair', 'LabRoundStool')
owned = set()
for name in names:
    old = bpy.data.objects.get(name)
    if old:
        if old.get('museum_asset_generator') != tag:
            raise RuntimeError('Refusing to replace an untagged asset: '+name)
        owned.update([old, *old.children_recursive])
    elif (repo/'unity/VirtualMuseum/Assets/Museum/Models'/f'{name}.fbx').exists():
        raise RuntimeError('Existing FBX has no corresponding owned source: '+name)
preserved = {o.name: (o.as_pointer(), tuple(v for row in o.matrix_world for v in row))
             for o in bpy.data.objects if o not in owned}
for obj in sorted(owned, key=lambda o: o.type == 'EMPTY'):
    bpy.data.objects.remove(obj, do_unlink=True)


def material(label, color, roughness, metallic=0):
    name = 'Lab | '+label
    old = bpy.data.materials.get(name)
    if old:
        return old
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    m.roughness, m.metallic = roughness, metallic
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


vinyl = material('Graphite vinyl', (.055, .062, .064), .54)
polymer = material('Black polymer', (.025, .030, .033), .55)
steel = material('Brushed steel', (.48, .52, .54), .27, .85)
tyres = material('Rubber tyres', (.014, .017, .019), .82)
frame = material('Dark frame', (.12, .14, .145), .43, .05)
parts = []


def finish(o, name, mat, smooth=False):
    o.name = asset_name+' | '+name
    o.data.materials.append(mat)
    if smooth:
        for polygon in o.data.polygons:
            polygon.use_smooth = True
    parts.append(o)
    return o


def bevel(o, radius, segments=3):
    modifier = o.modifiers.new('Manufactured edge radius', 'BEVEL')
    modifier.width, modifier.segments = radius, segments
    o.modifiers.new('Weighted face normals', 'WEIGHTED_NORMAL')
    return o


def box(name, location, size, mat, radius=.005):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(o, name, mat)
    return bevel(o, radius) if radius else o


def rod(name, start, end, radius, mat, end_radius=None, edge=.0015, vertices=32):
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


def ring(name, center, radius, thickness, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=10,
        location=center, major_radius=radius, minor_radius=thickness)
    return finish(bpy.context.object, name, mat, True)


def tube(name, points, radius, mat, closed=False):
    curve = bpy.data.curves.new(asset_name+' | '+name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth, curve.bevel_resolution = radius, 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for point, position in zip(spline.points, points):
        point.co = (*position, 1)
    spline.use_cyclic_u = closed
    o = bpy.data.objects.new(asset_name+' | '+name, curve)
    scene.collection.objects.link(o)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, name, mat, True)


def cushion(name, width, depth, height, roundedness=.5, crown=.004, wrap=0):
    """Closed rounded cushion with a shallow crown, rolled edge and flat base."""
    vertices, faces = [], []
    segments = 64
    profiles = [(0.86, -height*.5), (.97, -height*.32), (1, -height*.02),
                (.98, height*.29), (.90, height*.44), (.70, height*.50)]
    for size, z in profiles:
        for i in range(segments):
            angle = i*math.tau/segments
            c, s = math.cos(angle), math.sin(angle)
            x = math.copysign(abs(c)**roundedness, c)*width*.5*size
            y = math.copysign(abs(s)**roundedness, s)*depth*.5*size
            vertices.append((x, y, z+wrap*(x/(width*.5))**2))
    for row in range(len(profiles)-1):
        for i in range(segments):
            j = (i+1)%segments
            faces.append((row*segments+i, row*segments+j,
                          (row+1)*segments+j, (row+1)*segments+i))
    lower = len(vertices)
    vertices.append((0, 0, -height*.5))
    upper = len(vertices)
    vertices.append((0, 0, height*.5+crown))
    for i in range(segments):
        j = (i+1)%segments
        faces.append((lower, j, i))
        offset = (len(profiles)-1)*segments
        faces.append((upper, offset+i, offset+j))
    mesh = bpy.data.meshes.new(asset_name+' | '+name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    o = bpy.data.objects.new(asset_name+' | '+name, mesh)
    scene.collection.objects.link(o)
    return finish(o, name, vinyl, True)


def five_star_base():
    rod('Central moulded hub', (0, 0, .115), (0, 0, .190), .064, polymer,
        end_radius=.052, edge=.005)
    for i in range(5):
        a = math.tau*i/5 + math.pi/2
        direction = Vector((math.cos(a), math.sin(a), 0))
        tangent = Vector((-math.sin(a), math.cos(a), 0))
        verts = []
        for r, z, halfwidth, thick in [(.04, .156, .032, .040), (.255, .090, .021, .028)]:
            center = direction*r + Vector((0, 0, z))
            for side, up in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                verts.append(tuple(center+tangent*side*halfwidth+Vector((0, 0, up*thick*.5))))
        mesh = bpy.data.meshes.new(asset_name+' | tapered leg')
        mesh.from_pydata(verts, [], [(3,2,1,0),(4,5,6,7),(0,1,5,4),
                                    (1,2,6,5),(2,3,7,6),(3,0,4,7)])
        mesh.update()
        o = bpy.data.objects.new(asset_name+' | tapered leg', mesh)
        scene.collection.objects.link(o)
        bevel(finish(o, 'Five star tapered spoke', polymer), .009)
        caster_center = direction*.259 + Vector((0, 0, .032))
        swivel_angle = a + (.2 if i%2 else -.16)
        axle = Vector((-math.sin(swivel_angle), math.cos(swivel_angle), 0))
        rod('Caster swivel pin', caster_center+Vector((0,0,.028)),
            caster_center+Vector((0,0,.066)), .008, steel)
        cap=box('Caster fork housing', caster_center+Vector((0,0,.025)),
                (.048,.048,.028), polymer, .012)
        cap.rotation_euler.z=swivel_angle
        for side in (-1,1):
            wheel_center = caster_center+axle*(side*.025)
            rod('Twin caster tyre', wheel_center-axle*.010, wheel_center+axle*.010,
                .032, tyres, edge=.0035)
            hub = wheel_center+axle*(side*.0105)
            rod('Caster hub cover', hub-axle*.001, hub+axle*.001,
                .014, polymer, edge=.001)
    rod('Gas lift lower sleeve', (0,0,.158), (0,0,.346), .029, polymer, edge=.003)
    ring('Gas lift sleeve collar', (0,0,.335), .0285, .003, frame)
    rod('Polished gas piston', (0,0,.336), (0,0,.461), .018, steel, edge=.001)
    box('Seat mechanism housing', (0,0,.462), (.135,.16,.033), frame, .009)
    rod('Seat height lever shaft', (.052,-.015,.456), (.23,-.045,.448), .005, steel)
    grip=box('Seat height lever grip', (.238,-.048,.449), (.055,.025,.017), polymer, .008)
    grip.rotation_euler.z=-.17
    for x in (-.047,.047):
        for y in (-.05,.05):
            rod('Mechanism bolt', (x,y,.447), (x,y,.451), .006, steel, edge=.001, vertices=6)


export = runpy.run_path(str(repo/'work/export_static_fbx.py'))['export_selected_groups']
reports = []
for asset_name, display in [('LabSwivelChair',(7,0,0)), ('LabRoundStool',(8,0,0))]:
    parts = []
    five_star_base()
    if asset_name == 'LabSwivelChair':
        pan=box('Seat underside shell', (0,-.012,.484), (.416,.390,.034), polymer, .045)
        seat=cushion('Contoured vinyl seat', .435, .415, .065, roundedness=.43, crown=-.001)
        seat.location=(0,-.012,.507)
        # A broad, curved lower back and a metal height-adjustment support.
        tube('Bent back support', [(0,.103,.465),(0,.20,.457),(0,.253,.52),
             (0,.258,.66),(0,.256,.78)], .017, frame)
        box('Back support sliding collar', (0,.254,.645), (.068,.046,.10), polymer, .007)
        rod('Back height adjustment handwheel', (0,.27,.646), (0,.297,.646),
            .027, polymer, edge=.005)
        backing=box('Backrest moulded rear shell', (0,.215,.807), (.390,.035,.258), polymer, .035)
        backing.rotation_euler.x=math.radians(-10)
        back=cushion('Curved lumbar backrest', .410,.280,.060,roundedness=.46,crown=.002,wrap=.017)
        back.location=(0,.191,.805)
        back.rotation_euler.x=math.radians(80)
        for x in (-.09,.09):
            rod('Rear shell fastener', (x,.245,.795), (x,.249,.795), .006, frame,
                edge=.001, vertices=16)
    else:
        rod('Stool seat underside', (0,0,.476), (0,0,.493), .174, polymer,
            end_radius=.180, edge=.005, vertices=64)
        seat=cushion('Round padded vinyl seat', .375,.375,.060,roundedness=1,crown=.002)
        seat.location=(0,0,.508)
        ring('Seat perimeter welt', (0,0,.510), .187, .0019, polymer)
        ring('Polished foot ring', (0,0,.267), .210, .011, steel)
        rod('Foot ring clamp', (0,0,.247), (0,0,.282), .038, frame, edge=.003)
        for i in range(3):
            a=i*math.tau/3
            rod('Foot ring support', (math.cos(a)*.033,math.sin(a)*.033,.260),
                (math.cos(a)*.209,math.sin(a)*.209,.267), .008, steel)
    root = bpy.data.objects.new(asset_name,None)
    root['museum_asset_generator']=tag
    root['front_axis']='-Y'
    root['seat_height_m']=.540
    scene.collection.objects.link(root)
    for obj in parts:
        obj.parent=root
    bpy.context.view_layer.update()
    bounds=[obj.matrix_world@Vector(corner) for obj in parts for corner in obj.bound_box]
    size=[max(p[i] for p in bounds)-min(p[i] for p in bounds) for i in range(3)]
    if size[0]>.65 or size[1]>.65 or size[2]>1.02:
        raise RuntimeError('Seat unexpectedly exceeds its planned dimensions: '+str(size))
    report=export(repo/'unity/VirtualMuseum/Assets/Museum/Models'/f'{asset_name}.fbx',parts)
    root.location=display
    reports.append({'name':asset_name,'dimensions_m':size,'seat_height_m':root['seat_height_m'],**report})

bpy.context.view_layer.update()
for name,(pointer,matrix) in preserved.items():
    obj=bpy.data.objects.get(name)
    if not obj or obj.as_pointer()!=pointer or tuple(v for row in obj.matrix_world for v in row)!=matrix:
        raise RuntimeError('Unrelated source object changed: '+name)
bpy.ops.wm.save_as_mainfile(filepath=str(source))
print('LAB_SEATING',json.dumps(reports))
