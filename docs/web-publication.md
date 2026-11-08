# Web版のビルドとGitHub Pagesへの公開

UnityのWebGLビルドを `gh-pages` に置き、GitHub ActionsでGitHub Pagesに配信します。制作用の `main` と配信用の生成物は別のブランチに保持します。更新後はGitHub側のデプロイ完了と、公開URLへの反映を確認してください。[バーチャル展示室](https://virtual-museum.moukaeritai.work/)

## Unityでビルドする

1. Unity **6000.6.8f1** の **Web Build Support** をUnity Hubで追加しておきます。
2. `unity/VirtualMuseum/` をEditorで開き、Playを停止し、編集したシーンを保存します。
3. **Museum → Web → Build GitHub Pages** を実行します。
4. 成功すると `unity/VirtualMuseum/Build/WebGL/` に `index.html`、`museum-sw.js`、`manifest.webmanifest`、`favicon.svg`、`Build/`、詳細模型・室内データの `Content/` とライセンス表記を生成します。`Content/catalog.json` と `Content/room.json` の両方を保持してください。[室内データの遅延ロード](room-streaming.md)も参照してください。

このメニューは `MuseumWebBuild.Configure()` で設定してから `MuseumV1.unity` をビルドし、最後に `FinalizeOutput()` で `.nojekyll` と第三者素材・フォントのライセンス表記を付けます。手動で同じ設定を適用するメニューは **Museum → Web → Configure GitHub Pages** です。`Build/` はGitの追跡対象外です。

配信設定はBrotli圧縮とJavaScriptによるDecompression Fallbackを併用し、GitHub Pages側の独自HTTPヘッダー設定に依存しません。コードはDisk Size with LTO・IL2CPP OptimizeSize・Managed Stripping Highを使用し、ブラウザーから呼ぶメソッドを `link.xml` で保持します。WebGL 2を使い、スレッドは無効です。初期メモリは256 MB、上限は2048 MBです。[UnityのWeb配信設定](https://docs.unity3d.com/6000.6/Documentation/Manual/webgl-deploying.html)と[容量最適化の調査・手順](web-optimization.md)を参照してください。

## ブラウザーで確認する

生成物をHTTPサーバー経由で開いてください。`index.html` のダブルクリックによる `file://` での起動は確認方法にしません。日本語の表示、移動、標本の回転、顕微鏡、解説、体験済みのサイン、自動見学を確認します。

ローカル確認には `Build/WebGL/` を配信ルートにした静的HTTPサーバーを使います。Node・Playwright・Chromeを利用できる場合は、`node work/test_progressive_web.cjs` が一時サーバーを起動してモバイル操作と段階読み込みを検査し、終了時にサーバーも停止します。

マウス・キーボードと、移動パッド・タップ・ドラッグ・ピンチによるタッチ操作を用意しています。縦向きの狭い画面ではUnity内のUIを下部へまとめ、Web側も表示領域に合わせてキャンバスを伸縮します。観察から戻るときは、キーボードを使わず画面内の「戻る」を押せます。全画面に対応しないブラウザーでは通常表示のまま操作できます。

画面の左右の外側余白は原則2pxとし、ノッチなどの安全領域が大きい端末ではそちらを優先します。見学開始後はWeb側の上部ヘッダーを隠し、Unity内の見出しと下部の「操作案内」「全画面」を残して、展示室の表示領域を広げます。

小画面の確認では360 × 640程度の縦画面と640 × 360程度の横画面を使い、入口・読み込み・失敗表示・操作案内だけでなく、移動と見回しの同時操作、短いタップとドラッグの区別、標本回転・ピンチ、顕微鏡、展示一覧、解説、自動見学、画面回転も確認します。ブラウザーのタッチエミュレーションとスマートフォン実機での確認は区別してください。スマートフォン実機の動作・メモリ使用量・発熱・描画性能、SafariとFirefoxは未検証です。

2026年11月7日、Chromeのタッチエミュレーション（DPR 2、390 × 844、360 × 640、640 × 360）で実WebGLプレイヤーを起動し、移動パッドと見回しの同時入力、標本の回転・ピンチ、顕微鏡の拡大・移動と復帰、目的地ショートカット、FAQ、スクロール後のボタン、自動見学の開始・一時停止・次へ・終了、縦横切り替えを確認しました。1280 × 900のマウス・キーボード操作も再確認しています。これらの実行でブラウザーのエラーは発生していません。入口・読み込み・エラー表示などのWeb側は320 × 568を含む6寸法でも確認しています。

上記はタッチ対応時の確認記録です。その後の23点への展示拡張については、[拡張コレクションの検証範囲](expanded-collection.md#検証範囲)を別途参照してください。

WebテンプレートはキャンバスのCSS寸法とタッチ機能の有無を、`Museum experience` の `SetWebViewport(string)` にJSONで通知します。描画用のピクセル数に左右されずにUI寸法を決めるための情報です。外部の操作案内を開く間は `SetWebOverlay(string)` で展示室側の入力を止めます。いずれもプレイヤーの起動後に送信します。Unity側の入力・UIを変えたときはHTMLだけでなくWebGLプレイヤーも再ビルドしてください。

## マニフェストとファビコン

`Assets/WebGLTemplates/Museum/` の `manifest.webmanifest` と `favicon.svg` をWebビルドに同梱します。入口とスコープはマニフェストと同じディレクトリを指定し、アプリアイコンにもSVGを使います。配信ファイル一式を独立ドメインのルートに置いた場合も、これらの相対パスをそのまま使えます。

## 同じドメインのサービスワーカー

展示室は `museum-sw.js` をページと同じディレクトリから登録します。独自ドメインのスコープは `/` です。入口の小さなファイルと、選択後に取得した詳細模型をキャッシュします。[段階読み込みの構成・容量・検証](progressive-loading.md)

同じドメインの `/virtual-museum/` に配信する場合は、ルート側の Workbox の `navigateFallbackDenylist` にそのパスを含めます。ルート側のワーカーが有効なブラウザーで展示室を開き、展示室のコントローラーが `/virtual-museum/museum-sw.js` になったことを確認します。

## 配信用ブランチに送る

制作側の変更をコミットした後、リポジトリのルートで実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File work/publish_webgl.ps1
```

スクリプトはビルド済みファイルを検査し、追跡対象外の `unity/VirtualMuseum/Temp/pages-publish/` に配信専用のGit作業場所を作ります。`main` のチェックアウトは切り替えません。`origin` と同じGitHubリポジトリの `gh-pages` だけを更新し、強制プッシュはしません。Gitの認証と作者名・メールアドレスは制作側と同じ設定を使います。

送るのはWebプレイヤーの許可されたファイルだけです。編集用Blenderファイル、Unityプロジェクト、参考写真、ログなどを配信用ブランチへコピーしません。ビルドの主要ファイルとライセンス表記が足りない場合、100 MiB以上のファイルがある場合、配信用作業場所に未保存の変更や異なるリポジトリがある場合は、処理を止めます。既存の `gh-pages` に別の用途のファイルがある場合も上書きしません。

`publication.json` には制作側のコミットIDを保存します。再実行して配信内容が変わらない場合は、新しいコミットを作りません。通信エラーでプッシュに失敗した後など、配信作業場所に未送信コミットが残っている場合は、内容とリモートとの差分を確認してから復旧してください。スクリプトは履歴を破棄してやり直すことはしません。

## GitHub Pagesへ反映する

**Settings → Pages → Build and deployment** の公開元は **GitHub Actions** です。配信用ブランチへプッシュした後、**Actions → Deploy virtual museum → Run workflow** で `main` を選び、スクリプトが表示した `Published branch commit` の完全なSHAを入力します。ワークフローは `gh-pages` の先頭が指定されたSHAと一致することを確認して配信します。[GitHubの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

デプロイ成功後に公開URLを開き、`publication.json` の制作コミットとWebプレイヤーの起動を確認します。

UnityのビルドはこのPCで行います。GitHub上では生成済みの静的ファイルを配信するため、Unityのライセンス情報をGitHub Actionsのシークレットに登録する必要はありません。更新時はローカルで再ビルドし、確認してから同じ公開スクリプトを実行します。

## CLIを使う場合

EditorとUnity Pipelineに接続できる環境では、メニューの代わりに次の順で操作できます。再生は止めておきます。

```powershell
unity command script eval 'MuseumWebBuild.Configure(); MuseumProgressiveBuild.Prepare(); UnityEditor.SceneManagement.EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene()); return true;' --project-path unity/VirtualMuseum --json
unity command build run --target WebGL --output-path Build/WebGL --confirm --project-path unity/VirtualMuseum --json
unity command build status --project-path unity/VirtualMuseum --json
```

`build run` は非同期です。`build status` で成功を確認してから、次を実行します。

```powershell
unity command script eval 'MuseumWebBuild.FinalizeOutput(); return true;' --project-path unity/VirtualMuseum --json
```

その後のブラウザー確認・コミット・公開は上と同じです。コマンドは導入済みUnity CLIに依存するため、変更された場合は各コマンドのヘルプを確認してください。

## 同梱するフォントと素材

- 日本語フォント：Noto Sans JP、SIL Open Font License 1.1。配信物の `FONT-LICENSE.txt` と `THIRD-PARTY-NOTICES.txt` を保持します。元データ・取得先は `Assets/Museum/Resources/MuseumFonts/README.md` にあります。
- 壁・カーペット・木目の写真素材：CC0。詳細は[表面材質の出典](material-sources.md)にあります。
- 教材模型・生成した拡大模式図・試作キャラクターという制限はWeb版にも適用します。模型は実物標本のスキャンではなく、題材同士の大きさも実寸比ではありません。自由入力へのAI回答は実装していません。
