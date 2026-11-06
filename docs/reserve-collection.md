# 追加展示用の素材バンク

今後の展示追加に備えた25点の制作模型です。昆虫14点、化石5点、土器・石器6点を、現在の23点の展示とは別に管理します。**現行の展示室・移動先・自動見学にはまだ配置していません。**

Unity用のFBXは `Assets/Museum/Models/Reserve/`、抽出した材質は `Assets/Museum/Materials/Reserve/`、説明とモデルの対応表は `Assets/Museum/ReserveCollection.asset` です。いずれも `Resources/` 配下ではなく、現行シーンからも参照しないため、この素材バンクを用意するだけでは現在のWebGLプレイヤーへ同梱されません。

## 一覧

表のIDはFBXのファイル名に対応します。番号は素材バンク内の順番で、公開展示の番号とは別です。

| 番号 | 分類 | 模型 | ID | 主な観察箇所 |
|---:|---|---|---|---|
| 01 | 昆虫・成虫 | セミ | `Cicada` | 太い胸、複眼、翅の輪郭と翅脈 |
| 02 | 昆虫・成虫 | バッタ | `Grasshopper` | 跳躍する大きな後脚、体節、触角 |
| 03 | 昆虫・成虫 | ナナフシ | `StickInsect` | 枝のような細長い体と6本の脚 |
| 04 | 昆虫・成虫 | ハサミムシ | `Earwig` | 腹端のはさみ状の尾角、短い上翅 |
| 05 | 昆虫・成虫 | テントウムシ | `Ladybird` | 丸い上翅、模様、脚と触角 |
| 06 | 昆虫・成虫 | ホタル | `Firefly` | 軟らかい上翅、前胸、腹面の発光器を表す部分 |
| 07 | 昆虫・成虫 | ゾウムシ | `Weevil` | 長い口吻、触角、上翅の表面 |
| 08 | 昆虫・成虫 | アリ | `Ant` | くびれた腹柄、折れ曲がった触角、6本の脚 |
| 09 | 昆虫・幼虫 | アリジゴク | `AntlionLarva` | 大きな湾曲したあご、幅広い腹部、剛毛 |
| 10 | 昆虫・成虫 | カゲロウ | `Mayfly` | 大小2対の立てた翅、2本の長い尾、細い脚 |
| 11 | 昆虫・成虫 | クサカゲロウ | `Lacewing` | 網状の翅脈、屋根状の翅、長い触角、金色の眼 |
| 12 | 昆虫・成虫 | アメンボ | `WaterStrider` | 短い前脚、長い中脚と後脚、側面の銀色帯 |
| 13 | 昆虫・成虫 | カ | `Mosquito` | 1対の翅、平均棍、口吻、長い脚 |
| 14 | 昆虫・幼虫 | ボウフラ | `MosquitoLarva` | 脚のない体節、呼吸管、口の刷毛、剛毛束 |
| 15 | 化石 | 三葉虫の化石 | `TrilobiteFossil` | 頭部、分節した胴部、左右の葉と中央部 |
| 16 | 化石 | 直角石型の化石 | `OrthoconeFossil` | 先細りの殻、隔壁と気室を示す形 |
| 17 | 化石 | ウミユリの茎の化石 | `CrinoidStemFossil` | 円盤状の節が積み重なる茎 |
| 18 | 化石 | サメの歯の化石 | `SharkToothFossil` | 歯冠、根、縁の形 |
| 19 | 化石 | シダ状植物の化石 | `FernFossil` | 葉の並び、葉脈、母岩に残る形 |
| 20 | 土器 | 深鉢型の土器模型 | `EarthenwareDeepBowl` | 開いた口縁、器壁、内外面 |
| 21 | 土器 | 壺型の土器模型 | `EarthenwareJar` | 頸部、肩、胴部、底のつながり |
| 22 | 土器 | 土器片の模型 | `PotterySherd` | 湾曲した器壁、断面、表面の違い |
| 23 | 石器 | 磨製石斧の模型 | `PolishedStoneAxe` | 研磨した面と刃部の形 |
| 24 | 石器 | 打製石鏃の模型 | `KnappedArrowhead` | 尖頭部、左右の縁、剥離面 |
| 25 | 石器 | スクレイパーの模型 | `StoneScraper` | 厚み、剥離面、加工した縁 |

## 元データと再生成

| Blender元データ | 確認画像 | 生成スクリプト |
|---|---|---|
| [reserve_large_insects.blend](../blender/scenes/collections/reserve_large_insects.blend) | [大型の昆虫4点](../blender/previews/collections/reserve_large_insects.png) | [build_reserve_large_insects.py](../work/build_reserve_large_insects.py) |
| [reserve_small_insects.blend](../blender/scenes/collections/reserve_small_insects.blend) | [小型の昆虫・幼虫5点](../blender/previews/collections/reserve_small_insects.png) | [build_reserve_small_insects.py](../work/build_reserve_small_insects.py) |
| [reserve_winged_aquatic.blend](../blender/scenes/collections/reserve_winged_aquatic.blend) | [有翅・水生の昆虫5点](../blender/previews/collections/reserve_winged_aquatic.png) | [build_reserve_winged_aquatic.py](../work/build_reserve_winged_aquatic.py) |
| [reserve_fossils.blend](../blender/scenes/collections/reserve_fossils.blend) | [化石5点](../blender/previews/collections/reserve_fossils.png) | [build_reserve_fossils.py](../work/build_reserve_fossils.py) |
| [reserve_artifacts.blend](../blender/scenes/collections/reserve_artifacts.blend) | [土器・石器6点](../blender/previews/collections/reserve_artifacts.png) | [build_reserve_artifacts.py](../work/build_reserve_artifacts.py) |

各Blenderファイルには編集用の部品を残し、FBXへの書き出し用コピーだけを材質ごとにまとめています。生成スクリプトはリポジトリからの相対配置を使い、開いているBlenderとは別のバックグラウンドプロセスで実行します。再生成前に出力先と `--overwrite` の条件を確認してください。手動調整済みの元データ・FBXを未確認で上書きしないでください。

## Unityで準備する

1. 全25点のFBXが `Assets/Museum/Models/Reserve/` にあることを確認します。
2. Playを停止し、**Museum → Prepare Reserve Collection** を実行します。
3. `ReserveCollection.asset` に、モデル、表示名、英語見出し、説明、顕微鏡模式図の種類・注記を登録します。
4. FBXの材質を `Materials/Reserve/` に抽出して対応付けます。再実行時は既存材質とFBXの外部材質対応を再利用します。

この処理は現在開いているシーンを保存・作り直しせず、`ExpandedCollection.asset` も変更しません。素材バンクの説明や指定した透過・金属度の設定は、再実行するとスクリプトの定義で更新します。個別の手動調整を維持したい場合は差分を確認してから実行してください。

セミの翅膜はalpha 0.35、カゲロウ・クサカゲロウ・カの翅膜はalpha 0.24です。Unity StandardシェーダーではFade（`_Mode=2`、`SrcAlpha / OneMinusSrcAlpha`、深度書き込みOFF）に設定します。クサカゲロウの眼のMetallicは0.24、アメンボの銀色帯は0.12です。その他は不透明・非金属を基本とします。色と粗さはFBXから取り込んだ値を保持し、実際にインポートした材質と表示で確認します。

## 後で展示へ追加する

`ReserveCollection.asset` は素材一覧であり、現在の `Museum experience` のcollectionへそのまま差し替える操作はしません。現行の展示物・目的地・操作サインは、現行カタログの順番と対応しているためです。

追加するモデルを選び、現行の展示カタログ、配置、移動先、`MuseumExhibit.index`、操作サインを同じ対応で更新します。展示台に収まる縮尺と名札、観察用モデル、クリック対象、移動者が到着する空間を確認してください。モデルをシーンへドラッグしただけでは、一覧からの移動や回転観察の対象にはなりません。

配置後はUnityで読み込み・材質・回転観察・顕微鏡表示・移動・自動見学を確認し、Web版を更新する場合は再ビルドして公開します。[既存コレクション](expanded-collection.md)と[Web公開手順](web-publication.md)も参照してください。

## 模型の限界と検証

昆虫・化石は公開された博物館・大学などの形態資料を参考に独自制作した教材模型で、出典は各生成スクリプトの冒頭に記載しています。土器・石器は特定資料を複製せず、器壁・口縁・剥離面などを表現した汎用の制作模型です。実物標本や遺物のスキャンではなく、種・年代・産地・文化・用途を鑑定する資料としては使用できません。土器・石器は特定の遺跡や文化の遺物を複製したものではありません。

観察時の扱いやすさのため、FBXの最大寸法はおおむね1m、中心は原点にそろえています。相互の大きさは実寸比ではありません。細い毛や翅脈などを強調した表現も含みます。顕微鏡の登録情報は既存の生成模式図へ接続するためのもので、実物の顕微鏡写真や計測値を用意したという意味ではありません。

昆虫14点では、Blenderの保存済みファイルを再読込してレンダーを確認し、FBXの再インポートで原点・寸法・材質・形状を照合しています。化石・遺物も保存済みBlenderファイルのレンダーを確認しました。Unityでは全25点の読み込み、材質・シェーダー参照、最大寸法、三角形数と一覧レンダーを確認しています。現行展示へ未配置のため、来館者の操作経路やWebGLでの表示性能まで検証したモデルとしては扱いません。


[Unityでの全25点の表示確認](../blender/previews/collections/reserve_unity.png)。モデルごとの三角形数は168〜20,116、Renderer数は1〜7です。
