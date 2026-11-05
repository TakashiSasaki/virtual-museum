"""Give each shared collection its own editable scene in its source library."""
import bpy

collections = sorted((c for c in bpy.data.collections if c.asset_data), key=lambda c: c.name)
assert collections
scenes = []
for coll in collections:
    scene = bpy.data.scenes.new('編集 | ' + coll.name)
    scene.collection.children.link(coll)
    scenes.append(scene)
bpy.context.window.scene = scenes[0]
for old in list(bpy.data.scenes):
    if old not in scenes:
        bpy.data.scenes.remove(old)
text = bpy.data.texts.new('アセットの編集方法')
text.write('各アセットは別々のシーンにあります。画面右上のシーン選択から編集対象を選び、保存してください。\n'
           '展示室でライブラリを再読み込みすると変更が反映されます。原点は各アセットの床面です。\n')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('EDIT_SCENES', len(scenes), [s.name for s in scenes])
