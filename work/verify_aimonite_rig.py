"""Check source and FBX skeleton/skin without saving either asset.

Run on museum_v1_assets.blend in a background Blender process. A temporary
pose preview and JSON report are written under Unity's ignored Temp directory.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.kdtree import KDTree

source = Path(bpy.data.filepath)
if source.name != 'museum_v1_assets.blend':
    raise RuntimeError('Open the V1 source asset file')
repo = source.resolve().parents[2]
temporary = repo/'unity/VirtualMuseum/Temp'
temporary.mkdir(exist_ok=True)
fbx = repo/'unity/VirtualMuseum/Assets/Museum/Models/Aimonite.fbx'
root = bpy.data.objects['Aimonite']
rig = next(o for o in root.children_recursive if o.type == 'ARMATURE')
source_objects = [o for o in root.children_recursive if o.type == 'MESH']
report = {}


def weights(objects, armature):
    problems = []
    vertices = 0
    for obj in objects:
        if not any(m.type == 'ARMATURE' and m.object == armature for m in obj.modifiers):
            problems.append(obj.name + ': no armature modifier')
        names = {g.index: g.name for g in obj.vertex_groups}
        for vertex in obj.data.vertices:
            vertices += 1
            total = sum(group.weight for group in vertex.groups if names[group.group] in armature.data.bones)
            if abs(total - 1) > .00001:
                problems.append(obj.name + ': unnormalized vertex ' + str(vertex.index))
                break
    return {'meshes': len(objects), 'vertices': vertices, 'problems': problems}


def capture(objects, origin):
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    state = {}
    for obj in objects:
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        matrix = origin.inverted() @ evaluated.matrix_world
        points = [tuple(matrix @ v.co) for v in mesh.vertices]
        state[obj.name] = points
        evaluated.to_mesh_clear()
    return state


def bone_positions(armature, origin):
    matrix = origin.inverted() @ armature.matrix_world
    return {b.name: tuple(matrix @ b.head_local) for b in armature.data.bones}


def pose(armature):
    for bone in armature.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = Quaternion()
    # World-X flexion expressed in each bone's own rest axes also works after
    # an FBX importer has changed a bone's display orientation.
    for name, angle in {'AM_Thigh_L': .60, 'AM_Shin_L': -1.10, 'AM_Foot_L': .50,
                        'AM_UpperArm_L': .30, 'AM_Forearm_L': .50,
                        'AM_UpperArm_R': -.10}.items():
        bone = armature.pose.bones[name]
        axis = bone.bone.matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
        bone.rotation_quaternion = Quaternion(axis, angle)
    bpy.context.view_layer.update()


def maximum_motion(before, after, prefix):
    motion = []
    for name, points in before.items():
        if name.startswith(prefix):
            motion.extend((Vector(a)-Vector(b)).length for a, b in zip(points, after[name]))
    return max(motion, default=0)


def compare(expected, actual):
    mismatched_names = sorted(set(expected) ^ set(actual))
    largest = 0
    largest_mesh = None
    vertex_count_mismatches = []
    for name in set(expected) & set(actual):
        a, b = expected[name], actual[name]
        if len(a) != len(b):
            vertex_count_mismatches.append(name)
        tree = KDTree(len(b))
        for i, point in enumerate(b):
            tree.insert(point, i)
        tree.balance()
        # Check all control points rather than only the overall bounding box.
        error = max(tree.find(point)[2] for point in a)
        if error > largest:
            largest, largest_mesh = error, name
    return {'mismatched_names': mismatched_names, 'vertex_count_mismatches': vertex_count_mismatches,
            'maximum_surface_error_m': largest, 'largest_error_mesh': largest_mesh}


report['source_weights'] = weights(source_objects, rig)
report['source_bones'] = sorted(b.name for b in rig.data.bones)
assert len(rig.data.bones) == 12, report['source_bones']
assert not report['source_weights']['problems'], report['source_weights']
source_bones = bone_positions(rig, root.matrix_world)
source_rest = capture(source_objects, root.matrix_world)
pose(rig)
source_pose = capture(source_objects, root.matrix_world)
report['pose_motion_m'] = {prefix: maximum_motion(source_rest, source_pose, prefix)
                           for prefix in ['Boot', 'Brush tip', 'Left arm', 'Seal', 'Shell', 'Face']}
assert report['pose_motion_m']['Boot'] > .03
assert report['pose_motion_m']['Brush tip'] > .05
assert report['pose_motion_m']['Left arm'] > .03
assert report['pose_motion_m']['Shell'] < .00001
assert report['pose_motion_m']['Face'] < .00001

# Unity's standard skinned renderer uses linear blend skinning. FBX does not
# retain Blender's optional dual-quaternion Preserve Volume mode, so compare
# the identical skinning method as well as measuring any source-only delta.
for obj in source_objects:
    for modifier in obj.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.use_deform_preserve_volume = False
source_linear_pose = capture(source_objects, root.matrix_world)
report['preserve_volume_difference'] = compare(source_pose, source_linear_pose)

# This is only a pose check, not a time-driven walking demonstration.
scene = bpy.context.scene
for obj in scene.objects:
    if obj.type not in {'CAMERA', 'LIGHT'}:
        obj.hide_render = obj != root and obj not in root.children_recursive
    if obj.type == 'LIGHT':
        obj.hide_render = True
root.location = (0, 0, 0)
for pos, power, size in [((-3, -4, 5), 650, 4), ((3, 2, 4), 700, 3)]:
    bpy.ops.object.light_add(type='AREA', location=pos)
    lamp = bpy.context.object
    lamp.data.energy = power
    lamp.data.size = size
    lamp.rotation_euler = (Vector((0, 0, 1.2))-lamp.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.location = (2.5, -6, 1.5)
scene.camera.rotation_euler = (Vector((0, 0, 1.13))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.type = 'ORTHO'
scene.camera.data.ortho_scale = 2.65
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.filepath = str(temporary/'aimonite_pose_check.png')
bpy.ops.render.render(write_still=True)

# A fresh background-only file removes all source meshes/bind matrices from
# memory, so the following test cannot accidentally use the source skeleton.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False)
imported_rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
assert len(imported_rigs) == 1
imported_rig = imported_rigs[0]
imported_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
from mathutils import Matrix
report['fbx_weights'] = weights(imported_objects, imported_rig)
report['fbx_bones'] = sorted(b.name for b in imported_rig.data.bones)
report['rest_roundtrip'] = compare(source_rest, capture(imported_objects, Matrix.Identity(4)))
imported_bones = bone_positions(imported_rig, Matrix.Identity(4))
report['bone_position_error_m'] = max((Vector(position)-Vector(imported_bones[name])).length
                                     for name, position in source_bones.items())
pose(imported_rig)
report['posed_roundtrip'] = compare(source_linear_pose, capture(imported_objects, Matrix.Identity(4)))
report['saved_source'] = False
report_path = temporary/'aimonite_rig_verification.json'
report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('AIMONITE_RIG_VERIFICATION', json.dumps(report))
assert not report['fbx_weights']['problems'], report['fbx_weights']
assert report['fbx_bones'] == report['source_bones']
assert report['bone_position_error_m'] < .0001
for name in ['rest_roundtrip', 'posed_roundtrip']:
    assert not report[name]['mismatched_names'], report[name]
    assert report[name]['maximum_surface_error_m'] < .0001, report[name]
