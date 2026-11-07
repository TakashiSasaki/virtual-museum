# モバイルWebの起動容量を減らす

2026年11月7日の調査とローカル検証。公開への反映は別工程です。

この文書の16.70 MBは室内分割前の測定です。その後、[室内データも遅延ロード](room-streaming.md)にし、起動用を6.95 MBにしました。入室後の追加15.43 MBと区別して計測しています。

## ランタイムと素材は別々に測る

直前の段階読み込み版は起動用ファイル等が26.96 MB、うちWasmが8.28 MB、データが18.51 MBでした。WasmにはUnityエンジンとアプリのコードが含まれます。この8.28 MBがUnity一般の下限という意味ではありません。素材側の比率も大きく、コンテンツの軽量化は有効です。

コード容量優先設定とBrotliに変更した中間ビルドでは、Wasmは4,335,835 bytes、データは15,538,704 bytes、Buildディレクトリ合計は20,064,877 bytesでした。複数設定を同時に変えているため、減少量を個別設定の効果には分解していません。

フォント最適化後の最終ビルドは、Wasmが4,335,835 bytes、データが12,139,260 bytes、Buildディレクトリ合計が16,665,433 bytes。入口・ライセンス等を含め、詳細模型のContentを除く合計は16,701,761 bytesです。MBは1,000,000 bytesです。フォント変更だけで配信用データは約3.40 MB小さくなりました。

UnityのDetailedBuildReportで同梱フォントが約211 KBであることを確認し、ビルドのエラー・警告は0件でした。Chromeの新規モバイルコンテキストでBrotliのJavaScript解凍を含む起動、段階読み込み・失敗と再試行・キャッシュ検査が成功しました。日本語と模型はスクリーンショットでも確認しています。実機や実際の低速回線の時間・発熱は未測定です。

`work/test_web_ui.cjs` では実際のモバイルUIをタップし、標本観察から顕微鏡への切り替え、アイモナイト君の吹き出し、自動見学の開始・次へ・終了を検査しました。出力画像を目視確認し、予期しないブラウザー/Unityエラーは0件でした。`work/test_progressive_web.cjs` と同じNode・Playwright・Chrome環境で再実行できます。

## 他の配信サービスの工夫

- [CrazyGamesの技術要件](https://docs.crazygames.com/requirements/technical/)は、モバイル向けホーム掲載の初期ダウンロードを20 MB以下としています。メニューの表示ではなく遊べる状態までの容量です。全サイト共通の規格ではありませんが、初回サイズを制約として扱っている実例です。
- [CrazyGamesの最適化ガイド](https://docs.crazygames.com/resources/optimization-tips/)はBrotli、Disk Size with LTO、IL2CPP OptimizeSize、コード除去、追加素材の後読みを推奨しています。
- [Pokiのエンジン比較](https://developers.poki.com/guide/web-engine)と[開発者の記事](https://poki.com/blog/building-web-browser-games-2026)もUnityの初期サイズを課題として扱っています。Web向けエンジンではエンジンコードが小さくなり得ますが、移行はアプリの作り直しを伴います。
- [CoatsinkのUnity事例](https://unity.com/resources/coatsink-ready-set-cook)ではAssetBundlesを用いて素材の到着を後にし、ロビーへ早く入れる構成にしています。

Poki向けの無圧縮推奨は配信サーバー側の圧縮が前提です。独自Content-Encodingを指定できないGitHub Pagesへそのままコピーせず、BrotliとUnityのJavaScript解凍を使用します。

## 採用した設定と維持する動作

`MuseumWebBuild.Configure()` がDiskSizeLTO、IL2CPP OptimizeSize、Managed Stripping High、stripEngineCode、stripUnusedMeshComponentsを設定します。JavaScriptのSendMessageから呼ぶ入口は `Assets/Museum/link.xml` に明示し、実際のWebプレイヤーでも検査します。例外処理は残し、対応端末を狭めるWasm新機能やスレッドは追加していません。

段階読み込み、軽量な入口、上限付き模型キャッシュは[段階読み込みの説明](progressive-loading.md)を参照してください。サービスワーカーは初回通信量を消せません。先読みを増やすだけでは入室時の通信と競合するため、入口だけを事前保存します。

## フォントを更新するとき

展示文・UIの固定文字を対象に、元フォント4,533,028 bytesから942コードポイント・211,008 bytesのMuseum JP Subsetを生成しました。原本は `source-assets/fonts/` に保存し、同梱フォントのパスとGUIDは維持します。追加の展示文が必要とする文字をビルド前に検査し、古いサブセットならビルドを止めます。

Python 3と[FontTools](https://fonttools.readthedocs.io/en/latest/subset/)が必要です。リポジトリのルートで実行します。

```powershell
python -m pip install --target unity/VirtualMuseum/Library/MuseumPython fonttools==4.68.0
python work/prepare_web_font.py
```

`Library/MuseumPython` はGit対象外です。Pythonを別パスで起動しても構いません。フォントと `Assets/Museum/Editor/FontSubset.json` を一緒に更新し、Unityのインポート完了後にビルドします。コード・カタログ・シーンのUnicodeエスケープも検査対象です。SIL OFLのライセンス・著作権情報を保持し、派生フォントの内部名は原本と区別します。

この方式は現在の固定テキストに合わせています。将来の自由入力・外部データ配信では、字種拡張またはフォントの追加配信が必要です。Editorの任意の新しい文章も再生成までは欠字になり得ます。
