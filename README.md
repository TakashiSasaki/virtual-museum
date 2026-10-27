# バーチャル展示室

愛媛大学ミュージアムの参考写真をもとに作成した、Blender 5.2の展示室構想です。自然史、アートと科学、資料と地域の3ゾーンを歩いて巡ることができます。寸法と一部の展示品は構想用の仮設定です。

- [展示室のBlenderファイル（共有アセットをリンク）](outputs/museum_walkthrough_linked.blend)
- [分割前の展示室ファイル](outputs/museum_walkthrough.blend)
- [展示室の使い方](outputs/展示室の使い方.md)
- [平面プレビュー](outputs/04_展示室平面.png)
- [自然史展示室](outputs/01_自然史展示室.png)・[アート展示室](outputs/02_アート展示室.png)・[資料展示室](outputs/03_資料展示室.png)

Blenderファイルには参考写真の一部が埋め込まれています。見学カメラはフレーム1〜840、24 fpsです。カメラ表示でタイムラインを再生するか、3Dビューで `Walk Navigation` を使用してください。

## 共有アセット

`outputs/museum_walkthrough_linked.blend` は、`outputs/shared/museum-assets/furniture.blend` と `exhibits.blend` を相対パスで参照します。ケース、閲覧台、展示台、ベンチ、彫刻、アザラシ模型を共有アセット化しています。移動・コピーするときは `outputs` フォルダー内の相対配置を保ってください。詳しい編集方法は[共有アセットの使い方](outputs/shared/museum-assets/README.md)を参照してください。

現在は、展示室と共有アセットを同じリポジトリ内で追跡する構成です。共有アセットは別プロジェクトでもリンクできますが、Git リポジトリとしてはまだ独立していません。今後、アセットの共有先や公開先が決まった時点で独立リポジトリと submodule に移せます。

`work/` には制作・確認時のPythonスクリプトを残しています。これらは作業時のWindows環境と添付画像の絶対パスを参照する記録であり、別環境で実行するにはパスや入力画像の準備が必要です。途中のレンダリング画像、Blender試作ファイル、ダウンロードしたアドオンの展開物はGitの追跡対象から除いています。
