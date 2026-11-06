"""Export static asset copies grouped by material, keeping source parts editable.

Call export_selected_groups(filepath, objects, passthrough=()) after positioning
the asset's parent at the export origin. The selected objects must be meshes with
one material each. Modifiers and custom normals are evaluated before joining.
Passthrough objects are exported intact, without being joined or modified.
Temporary export objects/meshes are removed even if export fails. This helper
does not save the blend or change the source objects' transforms or geometry.
"""
from collections import defaultdict
from pathlib import Path
import os

import bpy


def export_selected_groups(filepath, objects, passthrough=()):
    objects, passthrough = list(objects), list(passthrough)
    if not objects:
        raise ValueError('No static parts supplied for grouped export')
    if set(objects) & set(passthrough):
        raise ValueError('Grouped and passthrough export objects must be disjoint')
    for obj in objects:
        if obj.type != 'MESH' or len(obj.data.materials) != 1 or obj.data.materials[0] is None:
            raise ValueError('Expected a mesh with exactly one material: '+obj.name)
    if any(obj.type != 'MESH' for obj in passthrough):
        raise ValueError('Static FBX passthrough accepts only mesh objects')
    active_before = bpy.context.view_layer.objects.active
    selection_before = list(bpy.context.selected_objects)
    temporary = bpy.data.collections.new('Temporary grouped FBX export')
    bpy.context.scene.collection.children.link(temporary)
    generated_meshes = []
    combined = []
    source_vertices = 0
    filepath = Path(filepath)
    # A leading dot keeps Unity from importing a partial FBX. Stage beside the
    # final file so its relative texture paths still refer to the same folder.
    staged = filepath.with_name('.' + filepath.stem + '.pending.fbx')
    try:
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        groups = defaultdict(list)
        for source in objects:
            evaluated = source.evaluated_get(depsgraph)
            mesh = bpy.data.meshes.new_from_object(evaluated,
                preserve_all_data_layers=True, depsgraph=depsgraph)
            generated_meshes.append(mesh.name)
            source_vertices += len(mesh.vertices)
            copy = bpy.data.objects.new('Export copy '+source.name, mesh)
            temporary.objects.link(copy)
            copy.matrix_world = source.matrix_world.copy()
            groups[source.data.materials[0]].append(copy)
        for material, members in groups.items():
            bpy.ops.object.select_all(action='DESELECT')
            for member in members:
                member.select_set(True)
            bpy.context.view_layer.objects.active = members[0]
            if len(members) > 1:
                bpy.ops.object.join()
            merged = bpy.context.view_layer.objects.active
            merged.name = 'Material group '+material.name
            combined.append(merged)
        combined_vertices = sum(len(obj.data.vertices) for obj in combined)
        if combined_vertices != source_vertices:
            raise RuntimeError('Grouped export unexpectedly changed the evaluated vertex count')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in combined+passthrough:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = combined[0]
        bpy.ops.export_scene.fbx(filepath=str(staged), use_selection=True,
            object_types={'MESH'}, apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
            bake_anim=False, use_mesh_modifiers=True)
        os.replace(staged, filepath)
        return {'source_parts': len(objects), 'material_groups': len(combined),
                'passthrough_parts': len(passthrough), 'vertices': combined_vertices}
    finally:
        if staged.exists():
            staged.unlink()
        for obj in list(temporary.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(temporary)
        for name in generated_meshes:
            mesh = bpy.data.meshes.get(name)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection_before:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active_before
