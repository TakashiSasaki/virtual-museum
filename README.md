# バーチャル展示室

[Web版を開く](https://virtual-museum.moukaeritai.work/) — 「展示室に入る」から、同じページ内で見学できます。キーボード・マウス操作に加え、スマートフォン向けのタッチ操作と縦長画面のUIを用意しています。スマートフォン実機での動作・性能は未検証です。[Web版のビルド・更新・公開手順](docs/web-publication.md)。

Web版では、アイモナイト君・什器・室内の質感を入室後に順次読み込みます。昆虫の胸脚を軽量模型でも確認できるようにした版の起動用データは約8.1 MBです。[段階読み込みとバックヤード](docs/progressive-loading.md)・[室内データの分割](docs/room-streaming.md)

## バージョン1：操作できる1部屋のプロトタイプ

今回の制作対象は、収蔵棚・作業台・顕微鏡を配置した1部屋の展示室です。昆虫、水生生物、微生物、鉱物、剥製型模型、飼育箱など、回転・拡大して観察する教材模型を23点に拡張しています。初期のコガネムシ・チョウ・アンモナイトも、上翅・翅脈・殻の肋などが分かる新しい模型へ更新しました。顕微鏡の表示は引き続き模式図です。[23点の展示一覧・制作資料・検証範囲](docs/expanded-collection.md)。

ミツバチは6本脚の昆虫、クモは8本脚のクモ類として別々に紹介し、ゴキブリとシロアリは同じゴキブリ目の比較展示として中央の独立展示台にまとめます。模型は実物標本のスキャンではなく、相互の大きさも実寸比ではありません。巡回するアイモナイト君、固定解説とFAQ、移動ショートカット、自動見学を備えています。自由入力のAI回答とWindows版のビルドは対象外です。

壁の塗装、木製標本箱、カーペットには写真ベースの色・凹凸・粗さを設定しています。箱の蓋合わせ目・金具を加え、実体顕微鏡を双眼鏡筒・焦点調節ノブ・カメラ・LED照明のある造形へ更新しました。Blenderの元データもUnityと同じテクスチャを相対パスで参照します。[素材の出典](docs/material-sources.md)。

作業台まわりに背付き回転椅子3脚、丸い回転スツール2脚、台下引出3台、ワゴン2台を配置し、奥壁に両開き収納棚2台を追加しています。椅子は五本脚・双輪キャスター・昇降軸のある研究室用の造形です。

操作できる場所には、床の分割リングとアイコン・日本語の操作案内を組み合わせた光るサインを配置しています。観察する展示は金色、顕微鏡3か所は青緑、巡回するアイモナイト君は紫色です。サインをクリック・タップして観察や解説を開けるほか、キーボード操作では標本・顕微鏡に近づいて操作可能になるとEキーの案内に変わります。

一度観察や解説を体験した場所は、サインを残したままチェックマークと「体験済み」の表示へ変わります。床のリングはつながった輪になり、光の明滅が落ち着きます。体験済みの場所も何度でも操作でき、履歴はその回の見学中に保持します。

- Unityプロジェクト：`unity/VirtualMuseum/`（Unity 6000.6.8f1）
- 開くシーン：`Assets/Museum/Scenes/MuseumV1.unity`
- [起動・操作・制限事項](unity/README.md)
- [初期バージョン1の仕様](docs/version1-spec.md)
- [展示物の制作参考資料](docs/exhibit-references.md)
- [拡張した23点の展示](docs/expanded-collection.md)・[陸上の昆虫とクモ](blender/previews/collections/terrestrial.png)・[水生・幼虫・微生物](blender/previews/collections/aquatic_micro.png)・[鉱物・化石・剥製型模型・飼育箱](blender/previews/collections/minerals_habitat.png)・[ゴキブリ目の比較](blender/previews/collections/blattodea.png)
- Blender元データ：`blender/scenes/museum_v1_assets.blend`
- [モデル確認画像](blender/previews/museum_v1_assets.png)
- [展示室のプレビュー](outputs/v1/01_room.png)・[標本棚の質感](outputs/v1/03_shelf_materials.png)・[作業台の質感](outputs/v1/04_workbench_materials.png)
- [実体顕微鏡の造形](blender/previews/microscope_detail.png)・[ドイツ箱の造形](blender/previews/specimen_boxes_detail.png)・[床と壁の質感](outputs/v1/05_floor_materials.png)
- [什器追加後の作業台](outputs/v1/06_lab_furniture.png)・[回転椅子と丸椅子](blender/previews/lab_seating.png)・[追加収納家具](blender/previews/lab_storage.png)
- [操作場所を示す光るサイン](outputs/v1/10_interaction_wayfinding.png)・[近づいたときの操作案内](outputs/v1/11_wayfinding_ready.png)
- [体験済みに変化したサイン](outputs/v1/12_experienced_wayfinding.png)
- [提供された参考画像11点](references/README.md) — 展示室・顕微鏡の写真、アイモナイト君の造形資料。

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

`work/` には制作・確認時のPythonスクリプトを残しています。古いスクリプトには作業時のWindows環境と添付画像の絶対パスを参照するものがあり、別環境で実行するにはパスや入力画像の準備が必要です。拡張コレクションの生成スクリプトはリポジトリからの相対配置を使います。実行前に対象ファイルと上書き条件を確認してください。途中のレンダリング画像、Blender試作ファイル、ダウンロードしたアドオンの展開物はGitの追跡対象から除いています。

## リポジトリの構成

- `outputs/` — 上記の展示室と共有アセット。リンクされた `.blend` の相対配置を維持してください。
- `work/` — 展示室の制作・確認用スクリプト。
- `references/` — 提供された参考画像の一覧と、展示室・初期構想の資料8点。
- `.codex-remote-attachments/` — アイモナイト君の追加添付画像3点。元の添付パスを保持。
- `blender/scenes/` — 展示室用アセット、拡張コレクション4ファイル、初期作品のBlender編集用ファイル。
- `blender/previews/` — モデルと初期作品の確認画像。拡張コレクションは `collections/` 配下。
- `unity/VirtualMuseum/` — バージョン1のUnityプロジェクト。起動方法は `unity/README.md` を参照。

Blender の元データを `blender/` に置き、Unity で使う書き出しデータは Unity プロジェクトの `Assets/` 配下に配置してください。Unity の `Assets/`、`Packages/`、`ProjectSettings/` と `.meta` ファイルは Git で管理し、`Library/` 等の生成物は管理対象から除外します。

## バイナリファイル

`.blend` や画像なども Git LFS を使わず、通常の Git で管理します。大きなファイルを変更するたびに履歴の容量が増えるため、コミットするファイルを確認してください。

## 今後の追加展示用モデル

昆虫14点・化石5点・土器と石器6点の計25点を別の素材バンクとして用意しました。[一覧・元データ・確認画像・Unityでの利用方法](docs/reserve-collection.md)。現行の23点の展示室には未配置です。
