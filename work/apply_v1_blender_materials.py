"""Apply the V1 shared texture palette in the open Blender asset workshop.

Run inside interactive Blender, with museum_v1_assets.blend open and saved.
The image files remain in Unity's Assets folder and are referenced relatively.
Only the V1 workshop file is modified; shared assets and other scenes are not.
"""
import bpy
from pathlib import Path

current = Path(bpy.data.filepath)
if current.name != 'museum_v1_assets.blend' or bpy.data.is_dirty:
    raise RuntimeError('Open the saved, unmodified V1 asset file before applying materials')
root = current.resolve().parents[2]
folder = root / 'unity' / 'VirtualMuseum' / 'Assets' / 'Museum' / 'Textures'
for filename in ('Walnut.png', 'Laminate.png', 'PowderCoat.png', 'RubberMat.png'):
    if not (folder / filename).is_file():
        raise FileNotFoundError(folder / filename)


def material(name, filename, roughness, distance, scale):
    name = 'V1 surface | ' + name
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (620, 80)
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.location = (340, 80)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = 0
    tex = nodes.new('ShaderNodeTexImage')
    tex.location = (-200, 100)
    absolute_path = folder / filename
    tex.image = bpy.data.images.load(str(absolute_path), check_existing=True)
    tex.image.filepath = bpy.path.relpath(str(absolute_path)).replace('\\', '/')
    tex.image.alpha_mode = 'CHANNEL_PACKED'  # alpha is height, not opacity
    tex.projection = 'BOX'
    tex.projection_blend = .08
    tex.extension = 'REPEAT'
    coord = nodes.new('ShaderNodeTexCoord')
    coord.location = (-650, 80)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-440, 80)
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    bump = nodes.new('ShaderNodeBump')
    bump.location = (60, -100)
    bump.inputs['Strength'].default_value = .24
    bump.inputs['Distance'].default_value = distance
    links = m.node_tree.links
    links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    links.new(tex.outputs['Color'], shader.inputs['Base Color'])
    links.new(tex.outputs['Alpha'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return m


wood = material('Walnut', 'Walnut.png', .70, .006, 1.0)
laminate = material('White laminate', 'Laminate.png', .66, .003, 1.2)
steel = material('Powder-coated steel', 'PowderCoat.png', .67, .002, 1.5)
rubber = material('Green work mat', 'RubberMat.png', .84, .003, 1.5)

scene = bpy.data.scenes.get('Museum V1 | Asset workshop')
if not scene:
    raise RuntimeError('V1 asset workshop scene is missing')
counts = {'wood': 0, 'laminate': 0, 'steel': 0, 'rubber': 0}
for obj in scene.objects:
    if obj.type != 'MESH' or not obj.parent:
        continue
    parent, name = obj.parent.name, obj.name
    selected = None
    if parent == 'SpecimenShelf':
        if name.startswith(('Specimen drawer', 'Inclined display')):
            selected, key = wood, 'wood'
        elif name.startswith(('Shelf upright', 'Storage base', 'Door')) and not name.startswith('Door handle'):
            selected, key = steel, 'steel'
        elif name.startswith('Tray lining'):
            selected, key = laminate, 'laminate'
    elif parent == 'ObservationBench':
        if name == 'Bench top':
            selected, key = laminate, 'laminate'
        elif name.startswith(('Bench leg', 'Wall cabinet')):
            selected, key = steel, 'steel'
        elif name == 'Observation mat':
            selected, key = rubber, 'rubber'
    if selected:
        obj.data.materials.clear()
        obj.data.materials.append(selected)
        counts[key] += 1
if min(counts.values()) == 0:
    raise RuntimeError('Unexpected V1 model structure: ' + str(counts))
bpy.ops.wm.save_as_mainfile(filepath=str(current))
result = {'file': str(current), 'assigned': counts,
          'images': [bpy.path.relpath(str(folder / n)) for n in
                     ('Walnut.png', 'Laminate.png', 'PowderCoat.png', 'RubberMat.png')]}
