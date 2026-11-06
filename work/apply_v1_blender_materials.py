"""Apply the shared surface palette in the saved V1 Blender asset workshop.

Photographic maps stay in Unity's Assets/Museum/Textures/PBR folder. The
fallback PNGs keep their original RGB-color/alpha-height contract. This script
updates only shelf/bench materials and their metric UV layer, then saves the
existing workshop. It does not rebuild models or export FBX files.
"""
import bpy
import hashlib
import math
from pathlib import Path

current = Path(bpy.data.filepath)
if current.name != 'museum_v1_assets.blend' or bpy.data.is_dirty:
    raise RuntimeError('Open the saved, unmodified V1 asset file before applying materials')
root = current.resolve().parents[2]
folder = root / 'unity' / 'VirtualMuseum' / 'Assets' / 'Museum' / 'Textures'
scene = bpy.data.scenes.get('Museum V1 | Asset workshop')
if not scene:
    raise RuntimeError('V1 asset workshop scene is missing')
for filename in ('Walnut.png', 'Laminate.png', 'PowderCoat.png', 'RubberMat.png'):
    if not (folder / filename).is_file():
        raise FileNotFoundError(folder / filename)
UV_NAME = 'Museum surface metric'
used_images = set()


def pbr_path(name, suffix):
    if name:
        for extension in ('.jpg', '.png', '.jpeg'):
            path = folder / 'PBR' / (name + '_' + suffix + extension)
            if path.is_file():
                return path
    return None


def image_node(nodes, links, uv, path, color=True, location=(-500, 100)):
    node = nodes.new('ShaderNodeTexImage')
    node.location = location
    node.image = bpy.data.images.load(str(path), check_existing=True)
    node.image.filepath = bpy.path.relpath(str(path)).replace('\\', '/')
    node.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    node.image.alpha_mode = 'CHANNEL_PACKED'
    node.extension = 'REPEAT'
    links.new(uv.outputs['UV'], node.inputs['Vector'])
    used_images.add(node.image.filepath)
    return node


def material(name, filename, roughness, distance, scale, pbr=None,
             pbr_scale=1, normal_strength=.3, rough_min=0, rough_max=1, variation=0):
    name = 'V1 surface | ' + name
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.clear()
    links = m.node_tree.links
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (650, 100)
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.location = (360, 100)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = 0
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = UV_NAME
    uv.location = (-800, 100)
    base = pbr_path(pbr, 'BaseColor')
    photographic = base is not None
    tex = image_node(nodes, links, uv, base or folder / filename)
    if variation:
        info = nodes.new('ShaderNodeObjectInfo')
        info.location = (-500, 400)
        tone = nodes.new('ShaderNodeMath')
        tone.operation = 'MULTIPLY_ADD'
        tone.inputs[1].default_value = variation * 2
        tone.inputs[2].default_value = 1 - variation
        tone.location = (-260, 350)
        multiply = nodes.new('ShaderNodeVectorMath')
        multiply.operation = 'SCALE'
        multiply.location = (0, 250)
        links.new(info.outputs['Random'], tone.inputs[0])
        links.new(tex.outputs['Color'], multiply.inputs[0])
        links.new(tone.outputs[0], multiply.inputs['Scale'])
        links.new(multiply.outputs['Vector'], shader.inputs['Base Color'])
    else:
        links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    rough = pbr_path(pbr, 'Roughness') if photographic else None
    normal = pbr_path(pbr, 'NormalGL') if photographic else None
    height = pbr_path(pbr, 'Height') if photographic else None
    if rough:
        image = image_node(nodes, links, uv, rough, False, (-500, -220))
        remap = nodes.new('ShaderNodeMapRange')
        remap.location = (30, -170)
        remap.inputs['To Min'].default_value = rough_min
        remap.inputs['To Max'].default_value = rough_max
        links.new(image.outputs['Color'], remap.inputs['Value'])
        links.new(remap.outputs['Result'], shader.inputs['Roughness'])
    if normal:
        image = image_node(nodes, links, uv, normal, False, (-500, -530))
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.uv_map = UV_NAME
        normal_map.location = (30, -450)
        normal_map.inputs['Strength'].default_value = normal_strength
        links.new(image.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    elif height or not photographic:
        bump = nodes.new('ShaderNodeBump')
        bump.location = (50, -440)
        bump.inputs['Strength'].default_value = 1
        bump.inputs['Distance'].default_value = distance
        if height:
            image = image_node(nodes, links, uv, height, False, (-500, -530))
            links.new(image.outputs['Color'], bump.inputs['Height'])
        else:
            links.new(tex.outputs['Alpha'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return m, pbr_scale if photographic else scale, photographic


def metric_uv(obj, scale, rotate=False, vary=False):
    """Box projection in metres; horizontal grain on both front and top.

    A real UV layer lets Blender transform the photographic tangent normal map
    correctly. Bevel modifiers interpolate it at the narrow rounded edges.
    """
    mesh = obj.data
    uv = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
    dimensions = obj.matrix_world.to_scale()
    seed = int(hashlib.sha1(obj.name.encode('utf8')).hexdigest()[:8], 16) / 0xffffffff
    offset = (seed * 9.13, seed * 3.71) if vary else (0, 0)
    for face in mesh.polygons:
        axis = max(range(3), key=lambda n: abs(face.normal[n]))
        for loop_index in face.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            p = [vertex[i] * abs(dimensions[i]) for i in range(3)]
            if axis == 0:
                u, v = p[1], p[2]
            elif axis == 1:
                u, v = p[0], p[2]
            else:
                u, v = p[0], p[1]
            if rotate:
                u, v = -v, u
            uv.data[loop_index].uv = (u * scale + offset[0], v * scale + offset[1])
    mesh.uv_layers.active = uv


wood, wood_scale, wood_photo = material('Walnut', 'Walnut.png', .61, .00025, 1,
    pbr='Walnut', pbr_scale=1/.6, normal_strength=.28, rough_min=.30, rough_max=.67, variation=.035)
laminate, laminate_scale, _ = material('White laminate', 'Laminate.png', .62, .00012, 1.45)
steel, steel_scale, _ = material('Powder-coated steel', 'PowderCoat.png', .70, .00016, 1.7)
rubber, rubber_scale, _ = material('Green work mat', 'RubberMat.png', .84, .00018, 2)

counts = {'wood': 0, 'laminate': 0, 'steel': 0, 'rubber': 0}
for obj in scene.objects:
    if obj.type != 'MESH' or not obj.parent:
        continue
    parent, name = obj.parent.name, obj.name
    selected = None
    if parent == 'SpecimenShelf':
        if name.startswith(('Specimen drawer', 'Inclined display')):
            selected, key, scale = wood, 'wood', wood_scale
        elif name.startswith(('Shelf upright', 'Storage base', 'Door')) and not name.startswith('Door handle'):
            selected, key, scale = steel, 'steel', steel_scale
        elif name.startswith('Tray lining'):
            selected, key, scale = laminate, 'laminate', laminate_scale
    elif parent == 'ObservationBench':
        if name == 'Bench top':
            selected, key, scale = laminate, 'laminate', laminate_scale
        elif name.startswith(('Bench leg', 'Wall cabinet')):
            selected, key, scale = steel, 'steel', steel_scale
        elif name == 'Observation mat':
            selected, key, scale = rubber, 'rubber', rubber_scale
    if selected:
        obj.data.materials.clear()
        obj.data.materials.append(selected)
        metric_uv(obj, scale, rotate=key == 'wood' and wood_photo, vary=key == 'wood')
        counts[key] += 1
if min(counts.values()) == 0:
    raise RuntimeError('Unexpected V1 model structure: ' + str(counts))
bpy.ops.wm.save_as_mainfile(filepath=str(current))
result = {'file': str(current), 'assigned': counts, 'images': sorted(used_images)}
print(result)
