"""Add an editable deforming skeleton to the generated Aimonite character.

Call ``rig_character(root, created)`` after the generated meshes have been
parented to the Aimonite root. The function appends its new objects to created
and returns the armature. Export the selected meshes AND armature with
``object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False, bake_anim=False``.
The rest pose is kept in Blender; Unity's AimoniteGait drives the named bones
from actual travel distance rather than a time-only looping animation.
"""
import math
import bpy
import bmesh
from mathutils import Vector


def rig_character(root, created):
    if root.type != 'EMPTY' or any(o.type != 'MESH' for o in created):
        raise RuntimeError('Pass the generated Aimonite root and mesh list')
    if any(o.type == 'ARMATURE' for o in root.children_recursive):
        raise RuntimeError('Remove the old character hierarchy before rigging')
    bpy.context.view_layer.update()

    # These named joints correspond to the generated character's proportions.
    # Positive Z is up, and the character looks toward negative Y in Blender.
    joints = {
        'AM_Root': ((0, 0, 0), (0, 0, .12), None),
        'AM_Body': ((-.27, -.13, .55), (-.27, -.13, .95), 'AM_Root'),
        'AM_UpperArm_L': ((-.49, -.15, .70), (-.505, -.165, .46), 'AM_Body'),
        'AM_Forearm_L': ((-.505, -.165, .46), (-.52, -.18, .22), 'AM_UpperArm_L'),
        'AM_UpperArm_R': ((-.06, -.15, .68), (.06, -.17, .44), 'AM_Body'),
        'AM_Forearm_R': ((.06, -.17, .44), (-.02, -.23, .35), 'AM_UpperArm_R'),
    }
    for side, x in [('L', -.34), ('R', -.20)]:
        joints['AM_Thigh_' + side] = ((x, -.13, .55), (x, -.13, .28), 'AM_Body')
        joints['AM_Shin_' + side] = ((x, -.13, .28), (x, -.16, .07), 'AM_Thigh_' + side)
        joints['AM_Foot_' + side] = ((x, -.16, .07), (x, -.26, .07), 'AM_Shin_' + side)

    data = bpy.data.armatures.new('Aimonite articulated skeleton')
    rig = bpy.data.objects.new('AimoniteRig', data)
    bpy.context.scene.collection.objects.link(rig)
    rig.parent = root
    rig.show_in_front = True
    rig.data.display_type = 'OCTAHEDRAL'
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        for name, (head, tail, parent) in joints.items():
            bone = data.edit_bones.new(name)
            bone.head, bone.tail = head, tail
            if parent:
                bone.parent = data.edit_bones[parent]
                bone.use_connect = (bone.head-bone.parent.tail).length < .00001
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    def group(obj, bone, indices, weight=1.0):
        vertex_group = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone)
        vertex_group.add(indices, weight, 'REPLACE')

    def base_name(obj):
        # Blender appends .001 etc while old and replacement models coexist.
        return obj.name.rsplit('.', 1)[0] if obj.name.rsplit('.', 1)[-1].isdigit() else obj.name

    for obj in list(created):
        name = base_name(obj)
        local = obj.matrix_local
        center = local.translation
        side = 'L' if center.x < -.27 else 'R'
        bone = 'AM_Body'
        if name == 'Leg':
            bone = 'AM_Thigh_' + side
        elif name in {'White boot', 'Boot lace'}:
            bone = 'AM_Shin_' + side
        elif name.startswith('Boot'):
            bone = 'AM_Foot_' + side
        elif name == 'Right arm':
            bone = 'AM_UpperArm_R'
        elif name in {'Right forearm', 'Right hand'} or name.startswith('Seal'):
            bone = 'AM_Forearm_R'
        elif name == 'Left hand' or name.startswith('Brush'):
            bone = 'AM_Forearm_L'

        if name == 'Left arm':
            # A cylinder has no vertices at the elbow until its long edges are
            # divided. Smooth weights then bend the continuous yellow arm.
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            edges = [e for e in bm.edges if e.calc_length() > .08]
            if edges:
                bmesh.ops.subdivide_edges(bm, edges=edges, cuts=15, use_grid_fill=True)
            bm.to_mesh(obj.data)
            bm.free()
            start = Vector(joints['AM_UpperArm_L'][0])
            finish = Vector(joints['AM_Forearm_L'][1])
            axis = finish-start
            for vertex in obj.data.vertices:
                t = (local @ vertex.co-start).dot(axis)/axis.length_squared
                weight = max(0.0, min(1.0, (t-.42)/.16))
                weight = weight*weight*(3-2*weight)
                if weight < 1:
                    group(obj, 'AM_UpperArm_L', [vertex.index], 1-weight)
                if weight > 0:
                    group(obj, 'AM_Forearm_L', [vertex.index], weight)
        else:
            group(obj, bone, list(range(len(obj.data.vertices))))

        modifier = obj.modifiers.new('Aimonite bone deformation', 'ARMATURE')
        modifier.object = rig
        # Unity/FBX use linear blend skinning; keep Blender's posed preview
        # identical instead of enabling Blender-only dual-quaternion skinning.
        modifier.use_deform_preserve_volume = False
        for polygon in obj.data.polygons:
            # Curved arms, boots and legs should stay rounded while posed.
            if name in {'Left arm', 'Right arm', 'Right forearm', 'Leg', 'White boot'}:
                polygon.use_smooth = True

    # Round knee caps cover the joint between the leg and the tall boot.
    gold = next((o.data.materials[0] for o in created if base_name(o) == 'Leg'), None)
    if gold:
        for side, x in [('L', -.34), ('R', -.20)]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, location=(x, -.13, .28))
            cap = bpy.context.object
            cap.name = 'Knee joint ' + side
            cap.scale = (.024, .024, .024)
            cap.parent = root
            cap.data.materials.append(gold)
            for face in cap.data.polygons:
                face.use_smooth = True
            group(cap, 'AM_Shin_' + side, list(range(len(cap.data.vertices))))
            modifier = cap.modifiers.new('Aimonite bone deformation', 'ARMATURE')
            modifier.object = rig
            created.append(cap)

    created.append(rig)
    rig['rig_version'] = 1
    rig['runtime_driver'] = 'AimoniteGait: distance driven planted feet and two bone IK'
    bpy.context.view_layer.update()
    for obj in created:
        if obj.type == 'MESH' and any(not v.groups for v in obj.data.vertices):
            raise RuntimeError('Unweighted Aimonite mesh: ' + obj.name)
    return rig
