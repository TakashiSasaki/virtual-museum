# Virtual Museum

Blender での制作と Unity での展示・アプリ開発をまとめて管理するリポジトリです。

## ディレクトリ

- `blender/scenes/` — Blender の編集用 `.blend` ファイル。
- `blender/previews/` — レンダリングした確認用画像。
- `unity/VirtualMuseum/` — 今後作成する Unity プロジェクトの配置先（現時点では未作成）。

Blender の元データを `blender/` に置き、Unity で使う書き出しデータは Unity プロジェクトの `Assets/` 配下に配置してください。Unity の `Assets/`、`Packages/`、`ProjectSettings/` と `.meta` ファイルは Git で管理し、`Library/` 等の生成物は管理対象から除外します。

## バイナリファイル

`.blend` や画像なども Git LFS を使わず、通常の Git で管理します。大きなファイルを変更するたびに履歴の容量が増えるため、コミットするファイルを確認してください。

既存の Blender 作品は元の場所からコピーしています。元ファイルは変更していません。
