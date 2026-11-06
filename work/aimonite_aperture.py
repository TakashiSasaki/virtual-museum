"""Make a connected, rounded shell opening around Aimonite's head.

Call ``carve_aperture(shell, material)`` after creating the closed shell mesh,
before projecting the front emblems. Coordinates are in the shell's mesh space.
The helper changes only that object, creates no persistent cutter objects, and
does not save or export anything. The source parameters remain editable here.
"""
import math

import bpy
import bmesh
from mathutils import Vector


HEAD_CENTER = Vector((-.27, -.16, .80))
CAVITY_RADII = Vector((.270, .225, .305))
COLLAR_RADII = Vector((.290, .245, .325))
MOUTH_NORMAL = Vector((0, -.35, -.937)).normalized()
# Signed plane distance from the head centre, opposite the outward normal.
# The lower plane exposes a visibly larger opening while leaving both eyes clear.
MOUTH_PLANE = -.170
LIP_BEVEL = .006


def _mesh_object(name, vertices, faces, shell, material=None):
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
    finally:
        bm.free()
    obj = bpy.data.objects.new(name, mesh)
    # Matching the transform allows the helper to work before or after parenting.
    obj.matrix_world = shell.matrix_world.copy()
    bpy.context.scene.collection.objects.link(obj)
    if material is not None:
        mesh.materials.append(material)
    return obj


def _crown_collar(shell, material):
    """Closed upper ellipsoid cap, with its mouth facing down and forward."""
    n = MOUTH_NORMAL
    u = Vector((1, 0, 0))
    v = n.cross(u).normalized()
    radii = COLLAR_RADII
    support_squared = sum((radii[i] * n[i]) ** 2 for i in range(3))
    support = math.sqrt(support_squared)
    v_radius = 1 / math.sqrt(sum((v[i] / radii[i]) ** 2 for i in range(3)))

    def section(q):
        center = HEAD_CENTER + Vector(tuple(
            radii[i] ** 2 * n[i] * q / support_squared for i in range(3)))
        factor = math.sqrt(max(0, 1 - q * q / support_squared))
        return center, radii.x * factor, v_radius * factor

    vertices = []
    faces = []
    rings, sides = 28, 128
    # A cosine parameter keeps the closed pole well resolved and smooth.
    start = math.acos(-MOUTH_PLANE / support)
    for i in range(rings):
        angle = start * (1 - i / rings)
        center, rx, rv = section(-support * math.cos(angle))
        for j in range(sides):
            a = math.tau * j / sides
            vertices.append(tuple(center + u * (rx * math.cos(a)) + v * (rv * math.sin(a))))
    for i in range(rings - 1):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, a + sides, b + sides, b))
    pole = len(vertices)
    vertices.append(tuple(section(-support)[0]))
    for j in range(sides):
        a = (rings - 1) * sides + j
        b = (rings - 1) * sides + (j + 1) % sides
        faces.append((a, pole, b))
    mouth_center = len(vertices)
    vertices.append(tuple(section(MOUTH_PLANE)[0]))
    for j in range(sides):
        faces.append((mouth_center, j, (j + 1) % sides))
    return _mesh_object('Temporary Aimonite crown collar', vertices, faces, shell, material)


def _head_cutter(shell):
    """Slight clearance around the head avoids skin/shell intersections."""
    vertices = [tuple(HEAD_CENTER + Vector((0, 0, CAVITY_RADII.z)))]
    faces = []
    rings, sides = 64, 128
    for i in range(1, rings):
        theta = math.pi * i / rings
        for j in range(sides):
            phi = math.tau * j / sides
            vertices.append(tuple(HEAD_CENTER + Vector((
                CAVITY_RADII.x * math.sin(theta) * math.cos(phi),
                CAVITY_RADII.y * math.sin(theta) * math.sin(phi),
                CAVITY_RADII.z * math.cos(theta)))))
    south = len(vertices)
    vertices.append(tuple(HEAD_CENTER - Vector((0, 0, CAVITY_RADII.z))))
    for j in range(sides):
        faces.append((0, 1 + j, 1 + (j + 1) % sides))
    for i in range(rings - 2):
        for j in range(sides):
            a = 1 + i * sides + j
            b = 1 + i * sides + (j + 1) % sides
            faces.append((a, a + sides, b + sides, b))
    for j in range(sides):
        a = 1 + (rings - 2) * sides + j
        b = 1 + (rings - 2) * sides + (j + 1) % sides
        faces.append((a, south, b))
    return _mesh_object('Temporary Aimonite head clearance', vertices, faces, shell)


def _terminal_chamber(shell, material):
    """A growing curved tube joins the outer whorl to the large mouth.

    Its upper cap is buried in the original shell. The lower cap overlaps the
    crown collar, so exact union creates one continuous shell wall. Keeping the
    lower cap slightly inside the collar avoids coincident mouth faces.
    """
    n = MOUTH_NORMAL
    v = n.cross(Vector((1, 0, 0))).normalized()
    radii = COLLAR_RADII
    q = MOUTH_PLANE - .018
    support_squared = sum((radii[i] * n[i]) ** 2 for i in range(3))
    end = HEAD_CENTER + Vector(tuple(
        radii[i] ** 2 * n[i] * q / support_squared for i in range(3)))
    factor = math.sqrt(1 - q * q / support_squared)
    end_rx = radii.x * factor
    end_rv = factor / math.sqrt(sum((v[i] / radii[i]) ** 2 for i in range(3)))
    controls = (Vector((-.49, .03, 1.40)), Vector((-.49, .02, 1.20)),
                end - n * .14, end)

    vertices, faces = [], []
    rings, sides = 49, 128
    for i in range(rings):
        t = i / (rings - 1)
        a, b, c, d = controls
        center = ((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d)
        direction = (3*(1-t)**2*(b-a) + 6*(1-t)*t*(c-b) + 3*t*t*(d-c)).normalized()
        u = direction.cross(Vector((0, 1, 0))).normalized()
        across = direction.cross(u).normalized()
        growth = t ** .75
        rx = .13 + (end_rx - .13) * growth
        rv = .15 + (end_rv - .15) * growth
        for j in range(sides):
            angle = math.tau * j / sides
            vertices.append(tuple(center + rx*math.cos(angle)*u + rv*math.sin(angle)*across))
    for i in range(rings - 1):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1) % sides
            faces.append((a, b, b+sides, a+sides))
    start_center = len(vertices)
    vertices.append(tuple(controls[0]))
    end_center = len(vertices)
    vertices.append(tuple(controls[-1]))
    for j in range(sides):
        faces.append((start_center, (j+1) % sides, j))
        faces.append((end_center, (rings-1)*sides+j, (rings-1)*sides+(j+1) % sides))
    return _mesh_object('Temporary Aimonite expanded terminal chamber', vertices, faces, shell, material)


def _apply_modifier(shell, modifier):
    with bpy.context.temp_override(
            object=shell, active_object=shell,
            selected_objects=[shell], selected_editable_objects=[shell]):
        result = bpy.ops.object.modifier_apply(modifier=modifier.name)
    if 'FINISHED' not in result:
        raise RuntimeError('Could not apply shell aperture modifier')


def _validate(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if not bm.faces or any(not e.is_manifold for e in bm.edges):
            raise RuntimeError('Shell aperture did not produce a closed manifold')
        remaining = set(bm.verts)
        connected = 0
        while remaining:
            connected += 1
            pending = [remaining.pop()]
            while pending:
                vertex = pending.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in remaining:
                        remaining.remove(other)
                        pending.append(other)
        if connected != 1 or bm.calc_volume(signed=True) <= 0:
            raise RuntimeError('The collar must be connected to one outward-facing shell')
        bm.to_mesh(mesh)
        return {'vertices': len(bm.verts), 'faces': len(bm.faces), 'connected_shells': connected}
    finally:
        bm.free()


def carve_aperture(shell, material):
    """Fuse a crown collar, carve the head cavity, and round the mouth edge.

    The caller must provide a closed mesh in Object mode. All temporary objects
    and modifiers are removed. On failure the original mesh is restored and the
    exception propagates, so the calling builder can retain the previous model.
    """
    if shell.type != 'MESH' or shell.mode != 'OBJECT':
        raise ValueError('The shell must be a mesh in Object mode')
    if shell.modifiers:
        raise ValueError('Apply existing shell modifiers before carving its opening')
    original = shell.data
    shell.data = original.copy()
    temporary = []
    success = False
    try:
        if material.name not in shell.data.materials:
            shell.data.materials.append(material)
        chamber = _terminal_chamber(shell, material)
        temporary.append(chamber)
        grow = shell.modifiers.new('Expand outer terminal chamber', 'BOOLEAN')
        grow.operation = 'UNION'
        grow.solver = 'EXACT'
        grow.object = chamber
        _apply_modifier(shell, grow)

        collar = _crown_collar(shell, material)
        temporary.append(collar)
        union = shell.modifiers.new('Fuse crown collar', 'BOOLEAN')
        union.operation = 'UNION'
        union.solver = 'EXACT'
        union.object = collar
        _apply_modifier(shell, union)

        cutter = _head_cutter(shell)
        temporary.append(cutter)
        cut = shell.modifiers.new('Carve head aperture', 'BOOLEAN')
        cut.operation = 'DIFFERENCE'
        cut.solver = 'EXACT'
        cut.object = cutter
        _apply_modifier(shell, cut)

        bevel = shell.modifiers.new('Round shell mouth', 'BEVEL')
        bevel.width = LIP_BEVEL
        bevel.segments = 3
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = math.radians(38)
        bevel.use_clamp_overlap = True
        _apply_modifier(shell, bevel)
        details = _validate(shell.data)
        for polygon in shell.data.polygons:
            polygon.use_smooth = True
        shell.data.update()
        details.update({'mouth_plane': MOUTH_PLANE, 'lip_bevel': LIP_BEVEL})
        success = True
        return details
    finally:
        for obj in temporary:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for modifier in list(shell.modifiers):
            shell.modifiers.remove(modifier)
        if not success:
            failed = shell.data
            shell.data = original
            if failed.users == 0:
                bpy.data.meshes.remove(failed)
        elif original.users == 0:
            bpy.data.meshes.remove(original)
