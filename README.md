# バーチャル展示室

[Web版を開く](https://TakashiSasaki.github.io/virtual-museum/) — 「展示室に入る」から、同じページ内で見学できます。PCのキーボード・マウス向けです。[Web版のビルド・更新・公開手順](docs/web-publication.md)。

## バージョン1：操作できる1部屋のプロトタイプ

今回の制作対象は、収蔵棚・作業台・顕微鏡を配置した1部屋の展示室です。ダミー標本3点の回転・拡大、顕微鏡の模式図、巡回するアイモナイト君の簡易モデル、固定解説とFAQ、移動ショートカット、自動見学を実装しています。自由入力のAI回答とWindows版のビルドは対象外です。

壁の塗装、木製標本箱、カーペットには写真ベースの色・凹凸・粗さを設定しています。箱の蓋合わせ目・金具を加え、実体顕微鏡を双眼鏡筒・焦点調節ノブ・カメラ・LED照明のある造形へ更新しました。Blenderの元データもUnityと同じテクスチャを相対パスで参照します。[素材の出典](docs/material-sources.md)。

作業台まわりに背付き回転椅子3脚、丸い回転スツール2脚、台下引出3台、ワゴン2台を配置し、奥壁に両開き収納棚2台を追加しています。椅子は五本脚・双輪キャスター・昇降軸のある研究室用の造形です。

操作できる場所には、床の分割リングとアイコン・日本語の操作案内を組み合わせた光るサインを配置しています。標本3か所は金色、顕微鏡3か所は青緑、巡回するアイモナイト君は紫色です。サインをクリックして観察や解説を開けるほか、標本・顕微鏡に近づいて操作可能になるとEキーの案内に変わります。

一度観察や解説を体験した場所は、サインを残したままチェックマークと「体験済み」の表示へ変わります。床のリングはつながった輪になり、光の明滅が落ち着きます。体験済みの場所も何度でも操作でき、履歴はその回の見学中に保持します。

- Unityプロジェクト：`unity/VirtualMuseum/`（Unity 6000.6.8f1）
- 開くシーン：`Assets/Museum/Scenes/MuseumV1.unity`
- [起動・操作・制限事項](unity/README.md)
- [バージョン1の仕様](docs/version1-spec.md)
- Blender元データ：`blender/scenes/museum_v1_assets.blend`
- [モデル確認画像](blender/previews/museum_v1_assets.png)
- [展示室のプレビュー](outputs/v1/01_room.png)・[標本棚の質感](outputs/v1/03_shelf_materials.png)・[作業台の質感](outputs/v1/04_workbench_materials.png)
- [実体顕微鏡の造形](blender/previews/microscope_detail.png)・[ドイツ箱の造形](blender/previews/specimen_boxes_detail.png)・[床と壁の質感](outputs/v1/05_floor_materials.png)
- [什器追加後の作業台](outputs/v1/06_lab_furniture.png)・[回転椅子と丸椅子](blender/previews/lab_seating.png)・[追加収納家具](blender/previews/lab_storage.png)
- [操作場所を示す光るサイン](outputs/v1/10_interaction_wayfinding.png)・[近づいたときの操作案内](outputs/v1/11_wayfinding_ready.png)
- [体験済みに変化したサイン](outputs/v1/12_experienced_wayfinding.png)

## 以前の展示室構想（保持）

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

## リポジトリの構成

- `outputs/` — 上記の展示室と共有アセット。リンクされた `.blend` の相対配置を維持してください。
- `work/` — 展示室の制作・確認用スクリプト。
- `blender/scenes/` — 初期のギャラリーとサッカーボールの Blender 編集用ファイル。
- `blender/previews/` — 初期作品のレンダリング画像。
- `unity/VirtualMuseum/` — バージョン1のUnityプロジェクト。起動方法は `unity/README.md` を参照。

Blender の元データを `blender/` に置き、Unity で使う書き出しデータは Unity プロジェクトの `Assets/` 配下に配置してください。Unity の `Assets/`、`Packages/`、`ProjectSettings/` と `.meta` ファイルは Git で管理し、`Library/` 等の生成物は管理対象から除外します。

## バイナリファイル

`.blend` や画像なども Git LFS を使わず、通常の Git で管理します。大きなファイルを変更するたびに履歴の容量が増えるため、コミットするファイルを確認してください。
