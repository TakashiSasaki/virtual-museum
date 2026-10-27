import bpy

text = bpy.data.texts['お読みください | 展示室の操作']
text.write('\n\n共有アセットについて\n'
           '展示ケース、閲覧台、展示台、ベンチと一部の模型は shared/museum-assets のファイルにリンクされています。\n'
           '位置は展示室内の「リンクされた共有アセット」で調整し、形状は共有ファイルの編集シーンで変更します。\n'
           '展示室を移動する際は shared/museum-assets フォルダーも相対位置を保って一緒に移動してください。\n')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
