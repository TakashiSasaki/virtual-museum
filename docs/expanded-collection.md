# 拡張コレクション：23点の観察模型

1部屋の展示室に、回転・拡大して観察する教材模型を23点登録しています。初期のコガネムシ・チョウ・アンモナイトは、それぞれ新しい `NaturalBeetle`、`SwallowtailButterfly`、`FossilAmmonite` へ置き換えます。旧ダミーのファイルは保持し、シーン内の旧展示は無効化します。

各展示は展示物や金色のサインから観察でき、「展示一覧・移動」（小画面では「移動」）にも掲載します。観察画面では回転・拡大・リセット・顕微鏡表示への切り替え・展示室への復帰を共通の操作で行います。顕微鏡の画像は題材に合わせた生成模式図で、実物の顕微鏡写真や、3Dモデルから計測した微細構造ではありません。

## 展示一覧

番号・表示名・FBX名は `Assets/Museum/Editor/MuseumCollectionSetup.cs` の登録順に対応します。

| 番号 | 展示名 | FBX名 | 主な観察箇所 |
|---:|---|---|---|
| 01 | コガネムシの仲間 | `NaturalBeetle` | 上翅、中央の合わせ目、節のある6本の脚 |
| 02 | アゲハチョウの仲間 | `SwallowtailButterfly` | 前後2対の翅、翅脈、後翅の尾状突起 |
| 03 | アンモナイトの化石 | `FossilAmmonite` | 外側ほど太い巻き、肋、母岩との関係 |
| 04 | クワガタムシの仲間 | `StagBeetle` | 大あご、上翅、触角と脚の節 |
| 05 | トンボの成虫 | `Dragonfly` | 複眼、透明な翅と翅脈、長い腹部 |
| 06 | ミツバチの仲間 | `Honeybee` | 6本の脚、胸部の毛、2対の翅、後脚 |
| 07 | カマキリの仲間 | `Mantis` | 三角形の頭、長い前胸、棘のある前脚 |
| 08 | ゲンゴロウの仲間 | `DivingBeetle` | 流線形の体、上翅、水かき状の後脚と毛 |
| 09 | タイコウチの仲間 | `WaterScorpion` | 幅広い体、捕獲用の前脚、腹端の呼吸管 |
| 10 | トンボの幼虫・ヤゴ | `DragonflyNymph` | 6本の脚、翅芽、腹部の節 |
| 11 | トビケラの幼虫 | `CaddisflyLarva` | 粒状の材料でできた巣、頭、3対の胸脚 |
| 12 | イモムシの体のつくり | `Caterpillar` | 頭、体節、胸脚と腹脚、気門 |
| 13 | ゾウリムシの拡大模型 | `Paramecium` | 繊毛、口溝、切開して見せる核・液胞 |
| 14 | ミドリムシの拡大模型 | `Euglena` | 鞭毛、眼点、切開して見せる内部構造 |
| 15 | 珪藻の拡大模型 | `Diatom` | 殻の輪郭、条線、孔、中央の縦溝 |
| 16 | 水晶の結晶群 | `QuartzCluster` | 六角柱、先端、集まった結晶面 |
| 17 | 黄鉄鉱の結晶群 | `PyriteCluster` | 立方体、金属光沢、面の条線 |
| 18 | カワセミの剥製型模型 | `KingfisherMount` | 嘴、重なった羽、枝をつかむ足 |
| 19 | リスの剥製型模型 | `SquirrelMount` | 尾、耳、前脚、毛の流れ |
| 20 | 中が見える飼育箱 | `RearingTerrarium` | 透明側面、床材、朽木、葉、内部の昆虫 |
| 21 | クモの体のつくり | `OrbWeaverSpider` | 頭胸部と腹部、8本の脚、小さな触肢 |
| 22 | ゴキブリの仲間 | `Cockroach` | 前胸背板、長い触角、棘のある6本の脚 |
| 23 | シロアリの仲間 | `Termite` | 淡い体、触角、腹部の形 |

ミツバチは6本脚の昆虫、クモは8本脚のクモ類として区別し、脚だけでなく体の区分も比較します。[Smithsonian「What is an insect?」](https://naturalhistory.si.edu/education/teaching-resources/life-science/what-insect)、[Australian Museum「What is a spider?」](https://australian.museum/learn/species-identification/ask-an-expert/what-is-a-spiders/)。

ゴキブリとシロアリは同じゴキブリ目（Blattodea）の比較展示として、室内中央奥の独立展示台に並べ、「ゴキブリ目 / ゴキブリとシロアリ」と表示します。シロアリをアリの仲間として扱わない構成です。分類の参考は、両者を同一の目として収蔵する[ロンドン自然史博物館のコレクション案内](https://www.nhm.ac.uk/our-science/services/collections/entomology/small-orders.html)です。

## 模型としての範囲

模型は公開された形態資料を参考に独自に制作したもので、実物標本のスキャンや特定種・個体の厳密な複製ではありません。参照先の写真をテクスチャへ転用していません。剥製型模型も、本物の剥製を撮影・計測したデータではありません。

FBXは観察時の扱いやすさを優先して最大寸法をおおむね1mにそろえ、Unityの展示台ごとに縮尺を調整します。昆虫・微生物・鉱物・鳥などを相互に同じ実寸比で並べた展示ではありません。とくに微生物は大きな拡大模型で、ゾウリムシとミドリムシは内部を見せる切開表現、珪藻は殻の細部を強調した表現を使います。

タイコウチは幅広い体の型、ヤゴは葉状の尾鰓を持たないトンボ亜目の型をイメージしています。イモムシでは3対の胸脚と、腹部の一部にある腹脚を区別します。これらは仲間による違いのすべてを表すものではありません。

顕微鏡画面の倍率は操作用の表示です。実際の機種の倍率・解像度、各模型の実寸、微細構造の計測値を保証する表示ではありません。

## 編集用元データと生成処理

| 元データ | 内容 | 生成スクリプト | 確認画像 |
|---|---|---|---|
| [terrestrial.blend](../blender/scenes/collections/terrestrial.blend) | 陸上の昆虫6点とクモ1点 | [build_terrestrial_collection.py](../work/build_terrestrial_collection.py) | [terrestrial.png](../blender/previews/collections/terrestrial.png) |
| [aquatic_micro.blend](../blender/scenes/collections/aquatic_micro.blend) | 水生昆虫・幼虫・微生物8点 | [build_aquatic_micro_collection.py](../work/build_aquatic_micro_collection.py) | [aquatic_micro.png](../blender/previews/collections/aquatic_micro.png) |
| [minerals_habitat.blend](../blender/scenes/collections/minerals_habitat.blend) | 鉱物2点、化石、剥製型模型2点、飼育箱 | [build_minerals_habitat.py](../work/build_minerals_habitat.py) | [minerals_habitat.png](../blender/previews/collections/minerals_habitat.png) |
| [blattodea.blend](../blender/scenes/collections/blattodea.blend) | ゴキブリ・シロアリ2点 | [build_blattodea_collection.py](../work/build_blattodea_collection.py) | [blattodea.png](../blender/previews/collections/blattodea.png) |

編集用の部品をBlenderに残し、Unity用のFBXは `unity/VirtualMuseum/Assets/Museum/Models/Collections/` へ書き出します。静的な部品は書き出し時に材質ごとにまとめ、模型の名前と材質の対応を保持します。初期の展示室・什器・アイモナイト君の元データは `blender/scenes/museum_v1_assets.blend` に引き続き保持します。

各スクリプトは、開いている作業用Blenderとは別のバックグラウンドプロセスで実行します。再生成するとそのスクリプトの担当する元データ・FBX・確認画像を書き換えるため、編集済みの部品を保存し、冒頭の出力先と上書き条件を読んでから実行してください。全スクリプトが同じ上書きオプションを持つわけではありません。

Unity側の `MuseumCollectionSetup.Apply()` は、23点の一覧、説明、顕微鏡模式図の種類を `Assets/Museum/ExpandedCollection.asset` へ保存し、拡張展示台・移動先・操作サインを設定します。**Museum → Expand Natural History Collection** はPlayを停止し、`MuseumV1.unity` を保存してから実行します。再実行すると **Expanded collection displays** 配下を作り直すので、その配下の手動調整を残す場合は先に差分を確認してください。

展示台の名札は、割り当てた幅と高さに収まるよう同梱フォントの描画寸法を測って縮小します。横並びの展示では幅0.60m以内とし、大きな模型の名札は模型の手前に寄せています。**Museum → Fit Display Labels** では、模型や展示台を作り直さずに、24枚の上面ラベルと初期展示の側面英字名札3枚を調整できます。Play停止後に実行し、シーンを保存してください。

## 材質と透過

モデルの色・粗さ・金属光沢は材質で表現します。飼育箱のガラスと、トンボ・ミツバチの翅膜は透明度を持つため、FBXの色だけでなくUnity側の透過設定も必要です。`MuseumCollectionSetup` は材質を `Assets/Museum/Materials/Collections/` に作成してFBXへ対応付け、透明材質の描画順・ブレンド・深度書き込みを設定します。

飼育箱を回した際に中の模型が見えること、翅の表裏と翅脈が見えることはUnityの実画面で確認する項目です。Blenderのレンダリング結果だけで透過の一致は判断しません。ゾウリムシとミドリムシは膜に厚みを持たせた切開模型で、不透明の材質でも内部を観察できます。水晶は結晶面と色の違いによる表現で、光学的な屈折の再現を保証しません。

## 形態の参照資料

以下は制作時に形態を調べるために参照した資料です。画像・写真をダウンロードして模型に貼り付けたり、提供元の文章を展示へ転載したりする用途では使っていません。個別の追加参照先は各生成スクリプト冒頭にも記録しています。

- 昆虫の基本形：[Smithsonian](https://naturalhistory.si.edu/education/teaching-resources/life-science/what-insect)。甲虫・チョウ・カマキリ：[Australian Museumの甲虫](https://australian.museum/learn/species-identification/ask-an-expert/what-do-beetles-look-like/)、[チョウ類](https://australian.museum/learn/species-identification/ask-an-expert/what-do-butterflies-moths-and-skippers-look-like/)、[カマキリ](https://australian.museum/learn/animals/insects/praying-mantises-order-mantodea/)。
- ミツバチ：[University of Arkansasの解説](https://www.uaex.uada.edu/farm-ranch/special-programs/beekeeping/about-honey-bees.aspx)。クモ：[Australian Museum](https://australian.museum/learn/species-identification/ask-an-expert/what-is-a-spiders/)。
- ゲンゴロウ：[University of Minnesotaの標本写真資料](https://midge.cfans.umn.edu/vsmivp/coleoptera/coleopteraadult/dytiscidaeadult)。タイコウチ：[University of Maine](https://extension.umaine.edu/home-and-garden-ipm/fact-sheets/common-name-listing/water-scorpions/)。
- ヤゴ・トビケラ：[Missouri Department of Conservationのトンボ](https://mdc.mo.gov/discover-nature/field-guide/dragonflies)、[トビケラ幼虫](https://mdc.mo.gov/discover-nature/field-guide/caddisfly-larvae)。イモムシの脚：[University of California IPM](https://ipm.ucanr.edu/PMG/G/I-LP-GENL-KC.001.html)。
- ゾウリムシ：[国立環境研究所の形態資料](https://www.nies.go.jp/chiiki1/protoz/morpho/ciliopho/parameci.htm)。ミドリムシ：[University of Maryland](https://www.science.umd.edu/labs/delwiche/PSlife/lectures/Euglenophyta.html)。
- 珪藻：[Diatoms of North Americaの縦溝の説明](https://diatoms.org/glossary/Raphe)、[California Academy of Sciencesの形態用語集](https://researcharchive.calacademy.org/research/diatoms/overview/glossary.html)。
- 鉱物：[Oxford University Museum of Natural Historyの学習資料](https://learningzone.oumnh.ox.ac.uk/node/2168186)、[Amgueddfa Cymruの鉱物データベース](https://museum.wales/mineralogy-of-wales/database/?mineral=266)。アンモナイト：[Natural History Museum](https://www.nhm.ac.uk/discover/what-is-an-ammonite.html)。
- カワセミ：[RSPB](https://www.rspb.org.uk/birds-and-wildlife/kingfisher)。リス：[Woodland Trust](https://www.woodlandtrust.org.uk/trees-woods-and-wildlife/animals/mammals/red-squirrel/)。
- ゴキブリ目：[Natural History Museumの分類・収蔵資料](https://www.nhm.ac.uk/our-science/services/collections/entomology/small-orders.html)、[Australian Museumのゴキブリの形態](https://australian.museum/learn/animals/insects/cockroaches-order-blattodea/)。

## 検証範囲

4つのBlenderコレクションすべてでレンダリングとFBXの書き出し・再インポートを確認しました。水生・幼虫・微生物の8点では中心・最大寸法・三角形数・材質数も照合し、各点は4〜7材質、4,756〜19,896三角形です。

23点版について、Unityのコンパイルと実Playモードで次を確認しました。

- 全23点で観察画面と顕微鏡画面への切り替え処理を実行。
- モデル・材質の欠落は0件、非対応シェーダーは0件。
- 展示・顕微鏡・入口を含む25か所の移動先すべてで、移動者のカプセル形状と障害物の重なりなし。
- 自動見学の6段階を完了し、自由見学へ復帰。
- 飼育箱のガラスのアルファ値0.12、黄鉄鉱のMetallic値0.86を確認。
- 23点を含むWebGLビルドが成功。

移動先の重なり検査は到着位置の確認であり、すべての歩行経路や透明材質の全方向からの見え方を保証するものではありません。

今回のWebGLビルドはローカルHTTP配信でChromeの実行を確認しました。390×844のタッチ入力エミュレーションで一覧の末尾まで移動し、ミツバチ・ゴキブリ・シロアリ・クモ・飼育箱・ゾウリムシを選択して観察しました。指ドラッグによる回転、ピンチ拡大、顕微鏡への切り替え、展示室への復帰を確認し、飼育箱は回転した状態でも内部が見えます。ブラウザーエラーは0件でした。

描画領域は390×844の画面で386×800、360×640で356×596となり、左右の外側余白は各2ピクセルです。デスクトップの1280×900でも起動・矢印キー移動・右ドラッグ視点変更・標本観察・回転・ホイール拡大・復帰を確認しました。公開先ではデプロイ後に `publication.json` と起動動作を確認します。既存のタッチ対応時の確認記録は[Web公開手順](web-publication.md)にあります。スマートフォン実機、Safari、Firefoxでの動作・性能は未検証です。
