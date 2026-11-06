# 表面材質の出典

2026-11-06の調整で、次のCC0写真素材を使用しました。元の画像を1024 × 1024で取得し、Unity用のファイル名へ変更しています。樹種や実物の材質を鑑定したものではなく、参考写真に近い見え方のための素材です。

| 用途 | 素材・作者 | 撮影範囲 | 使用する情報 |
|---|---|---|---|
| 木製ドイツ箱・展示トレー | [Fine Grained Wood / Rob Tuytel](https://polyhaven.com/a/fine_grained_wood) | 0.6 m四方 | 色、法線、粗さ |
| 壁・天井の白い塗装面 | [White Plaster 02](https://polyhaven.com/a/white_plaster_02) | 1 m四方 | 色、法線、粗さ、高さ |
| カーペット | [Carpet016](https://ambientcg.com/view?id=Carpet016) | 1.7 m四方 | 色、法線、粗さ、高さ |

ライセンス：[Poly HavenのCC0条件](https://polyhaven.com/license)、[ambientCGのCC0条件](https://docs.ambientcg.com/license/)。詳細な取得先・サイズ・ハッシュは [pbr-sources.json](../work/pbr-sources.json) に記録しています。

保存先は `unity/VirtualMuseum/Assets/Museum/Textures/PBR/` です。色の画像はsRGB、法線・粗さ・高さは線形として扱います。法線はOpenGL形式です。壁の色むらと凹凸は控えめに、木箱の木目は部材の長手方向に合わせ、箱ごとに採る模様と色味をわずかに変えています。カーペットには幅50 cmのごく細い継ぎ目を加えています。

白い机、塗装金属、作業マット、ビニル床は引き続き `work/generate_material_textures.py` の手続き生成素材を使います。画像生成AIによる素材は使用していません。
