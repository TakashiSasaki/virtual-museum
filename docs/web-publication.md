# Web版のビルドとGitHub Pagesへの公開

UnityのWebGLビルドを、このリポジトリの `gh-pages` ブランチからGitHub Pagesで配信します。制作用の `main` と配信用の生成物は別のブランチに保持します。公開先は <https://TakashiSasaki.github.io/virtual-museum/> です。更新後はGitHub側のPagesデプロイ完了と、URLへの反映を確認してください。

## Unityでビルドする

1. Unity **6000.6.8f1** の **Web Build Support** をUnity Hubで追加しておきます。
2. `unity/VirtualMuseum/` をEditorで開き、Playを停止し、編集したシーンを保存します。
3. **Museum → Web → Build GitHub Pages** を実行します。
4. 成功すると `unity/VirtualMuseum/Build/WebGL/` に `index.html`、`museum-sw.js`、`manifest.webmanifest`、`favicon.svg`、`Build/` とライセンス表記を生成します。

このメニューは `MuseumWebBuild.Configure()` で設定してから `MuseumV1.unity` をビルドし、最後に `FinalizeOutput()` で `.nojekyll` と第三者素材・フォントのライセンス表記を付けます。手動で同じ設定を適用するメニューは **Museum → Web → Configure GitHub Pages** です。`Build/` はGitの追跡対象外です。

配信設定はGzip圧縮とJavaScriptによるDecompression Fallbackを併用し、GitHub Pages側の独自HTTPヘッダー設定に依存しません。WebGL 2を使い、スレッドは無効です。初期メモリは256 MB、上限は2048 MBです。[UnityのWeb配信設定](https://docs.unity3d.com/6000.6/Documentation/Manual/webgl-deploying.html)を参照してください。

## ブラウザーで確認する

生成物をHTTPサーバー経由で開いてください。`index.html` のダブルクリックによる `file://` での起動は確認方法にしません。日本語の表示、移動、標本の回転、顕微鏡、解説、体験済みのサイン、自動見学を確認します。

導入済みCLIでは `unity build run unity/VirtualMuseum --build-path unity/VirtualMuseum/Build/WebGL` でローカル確認用のサーバーを起動できます。確認終了後は、そのコマンドをCtrl+Cで停止します。

マウス・キーボードと、移動パッド・タップ・ドラッグ・ピンチによるタッチ操作を用意しています。縦向きの狭い画面ではUnity内のUIを下部へまとめ、Web側も表示領域に合わせてキャンバスを伸縮します。観察から戻るときは、キーボードを使わず画面内の「戻る」を押せます。全画面に対応しないブラウザーでは通常表示のまま操作できます。

小画面の確認では360 × 640程度の縦画面と640 × 360程度の横画面を使い、入口・読み込み・失敗表示・操作案内だけでなく、移動と見回しの同時操作、短いタップとドラッグの区別、標本回転・ピンチ、顕微鏡、展示一覧、解説、自動見学、画面回転も確認します。ブラウザーのタッチエミュレーションとスマートフォン実機での確認は区別してください。スマートフォン実機の動作・メモリ使用量・発熱・描画性能、SafariとFirefoxは未検証です。

2026年11月7日、Chromeのタッチエミュレーション（DPR 2、390 × 844、360 × 640、640 × 360）で実WebGLプレイヤーを起動し、移動パッドと見回しの同時入力、標本の回転・ピンチ、顕微鏡の拡大・移動と復帰、目的地ショートカット、FAQ、スクロール後のボタン、自動見学の開始・一時停止・次へ・終了、縦横切り替えを確認しました。1280 × 900のマウス・キーボード操作も再確認しています。これらの実行でブラウザーのエラーは発生していません。入口・読み込み・エラー表示などのWeb側は320 × 568を含む6寸法でも確認しています。

WebテンプレートはキャンバスのCSS寸法とタッチ機能の有無を、`Museum experience` の `SetWebViewport(string)` にJSONで通知します。描画用のピクセル数に左右されずにUI寸法を決めるための情報です。外部の操作案内を開く間は `SetWebOverlay(string)` で展示室側の入力を止めます。いずれもプレイヤーの起動後に送信します。Unity側の入力・UIを変えたときはHTMLだけでなくWebGLプレイヤーも再ビルドしてください。

## マニフェストとファビコン

`Assets/WebGLTemplates/Museum/` の `manifest.webmanifest` と `favicon.svg` をWebビルドに同梱します。入口とスコープはマニフェストと同じディレクトリを指定し、アプリアイコンにもSVGを使います。配信ファイル一式を独立ドメインのルートに置いた場合も、これらの相対パスをそのまま使えます。

## 同じドメインのサービスワーカー

展示室は `museum-sw.js` をページと同じディレクトリから登録します。公開先でのスコープは `/virtual-museum/` です。展示室専用ワーカーはリクエストに応答せず、ブラウザー標準の通信とキャッシュに任せます。

初回アクセスで展示室のHTMLに届くよう、ドメイン直下のサイトでは Workbox の `navigateFallbackDenylist` に `/virtual-museum/` を含めます。ルート側のワーカーが有効なブラウザーから展示室を開き、開発者ツールで展示室のコントローラーが `/virtual-museum/museum-sw.js` になったことを確認します。

## 配信用ブランチに送る

制作側の変更をコミットした後、リポジトリのルートで実行します。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File work/publish_webgl.ps1
```

スクリプトはビルド済みファイルを検査し、追跡対象外の `unity/VirtualMuseum/Temp/pages-publish/` に配信専用のGit作業場所を作ります。`main` のチェックアウトは切り替えません。`origin` と同じGitHubリポジトリの `gh-pages` だけを更新し、強制プッシュはしません。Gitの認証と作者名・メールアドレスは制作側と同じ設定を使います。

送るのはWebプレイヤーの許可されたファイルだけです。編集用Blenderファイル、Unityプロジェクト、参考写真、ログなどを配信用ブランチへコピーしません。ビルドの主要ファイルとライセンス表記が足りない場合、100 MiB以上のファイルがある場合、配信用作業場所に未保存の変更や異なるリポジトリがある場合は、処理を止めます。既存の `gh-pages` に別の用途のファイルがある場合も上書きしません。

`publication.json` には制作側のコミットIDを保存します。再実行して配信内容が変わらない場合は、新しいコミットを作りません。通信エラーでプッシュに失敗した後など、配信作業場所に未送信コミットが残っている場合は、内容とリモートとの差分を確認してから復旧してください。スクリプトは履歴を破棄してやり直すことはしません。

## GitHub Pagesの初回設定

GitHubのリポジトリで **Settings → Pages → Build and deployment** を開きます。

- Source：**Deploy from a branch**
- Branch：**gh-pages**
- Folder：**/ (root)**

保存後、Pagesのデプロイ結果が成功になってから公開URLを開きます。ファイル送信の成功と、Pagesの反映・ブラウザーの動作確認は別の段階です。[GitHubの公開元設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

UnityのビルドはこのPCで行います。GitHub上では生成済みの静的ファイルを配信するため、Unityのライセンス情報をGitHub Actionsのシークレットに登録する必要はありません。更新時はローカルで再ビルドし、確認してから同じ公開スクリプトを実行します。

## CLIを使う場合

EditorとUnity Pipelineに接続できる環境では、メニューの代わりに次の順で操作できます。再生は止めておきます。

```powershell
unity command script eval 'MuseumWebBuild.Configure(); return true;' --project-path unity/VirtualMuseum --json
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
- ダミー標本・拡大模式図・試作キャラクターという既存の制限はWeb版にも適用します。自由入力へのAI回答は実装していません。
