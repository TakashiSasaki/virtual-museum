import bpy, os
scene=bpy.context.scene
scene.camera=bpy.data.objects['ウォークスルー カメラ']
scene.frame_set(1)
scene.render.filepath='//renders/'
scene.render.image_settings.file_format='PNG'
for name,frame in [('入口',1),('自然史',100),('アートと科学',350),('資料と地域',640),('帰路',840)]:
    if not scene.timeline_markers.get(name): scene.timeline_markers.new(name,frame=frame)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('USER_FILE_READY',bpy.data.filepath)
