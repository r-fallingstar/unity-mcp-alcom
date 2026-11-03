# Unity MCP for ALCOM

[CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) の非公式VPM配布用Forkです。元のMITライセンス・著作者・UnityのGUIDを維持し、ALCOMから導入・更新できます。

**[ALCOMに追加するページ](https://r-fallingstar.github.io/unity-mcp-alcom/)**

リポジトリURL:

```text
https://r-fallingstar.github.io/unity-mcp-alcom/index.json
```

ALCOMの「パッケージ管理」でリポジトリを追加し、対象プロジェクトで **MCP for Unity (ALCOM)** をインストールしてください。以降は同じ画面の更新操作で更新できます。ベータ版を使う場合はALCOMのプレリリース表示を有効にします。Python 3.10以上とuvは別途必要です。

## 既存の手動配置からの移行

1. 作業を保存して対象のUnityプロジェクトを閉じ、プロジェクトをバックアップします。
2. `Packages/com.coplaydev.unity-mcp` を手動で配置している場合は、そのフォルダーをプロジェクト外へ退避します。`Packages/manifest.json` にこのパッケージのGit URLやfile参照がある場合は、その項目を除きます。Assets配下に古いUnity MCPを配置している場合も重複しないよう退避します。
3. ALCOMから同パッケージをインストールします。パッケージIDは既存と同じ `com.coplaydev.unity-mcp` です。
4. Unityを開き、MCP for Unityウィンドウでローカルサーバーを再起動します。既存のサーバーURLの明示的な上書きは優先されます。同梱サーバーを使う場合はその上書きを解除してください。接続先は引き続きローカルに設定してください。

このForkは現在開いているプロジェクトやシーンを自動で書き換えません。

## 配布の仕組み

- 既定の `alcom` ブランチに配布スクリプトと小さなオーバーレイパッチを保持します。本家の `main`（安定版）と `beta` の新しいパッケージバージョンをGitHub Actionsで毎日確認します。手動実行も可能です。
- 各配布は本家の特定コミットから構築し、`provenance.json` にコミットを記録します。既に公開した同じバージョンは上書きしません。本家がバージョンを上げずに変更した場合は配布しません。
- Pythonサーバーを `Server~/<version>/` に同梱します。Python側のメタデータも対応する版に合わせます。明示的な設定がない場合、Unity側はこのローカルパスを使用します。PyPI上の別のベータ版が選ばれる問題を避けます。
- ZIPはルートに `package.json` を持ち、既存の `.meta` を維持します。VPM一覧にはSHA-256を記録します。公開前にパッケージテストと同梱サーバーの `--help` 起動確認を実行します。
- 本家の変更でパッチが適用できない場合は公開処理が失敗し、既存の配布一覧を維持します。更新処理の成功は実際のUnityプロジェクト全体の互換性を保証するものではありません。
- VPM一覧と追加ページは公式の `actions/deploy-pages` でGitHub Pagesへ直接公開します。認証は実行時の `GITHUB_TOKEN` とOIDCのみ使用し、個人用トークンは保存しません。
- 本家のPyPI公開・ドキュメント公開・統計用ワークフローは `alcom` ブランチから除いています。

## 開発・検証

クリーンな本家のbetaチェックアウトを `_upstream/beta` に置いて実行します。

```sh
python -m unittest discover -s alcom/tests -v
python alcom/build.py _upstream/beta dist/test
```

初回はActionsを有効にし、GitHub Pagesの配布元を `GitHub Actions` に設定します。Fork名・所有者を変える場合は `alcom/publish.py` と `alcom/index.html` のリポジトリURLも更新してください。

本家の使用方法は [README.upstream.md](README.upstream.md)、ライセンスは [LICENSE](LICENSE) を参照してください。

## このForkの保守への支援

ALCOM向けの配布は、これからも無料で提供していく予定です。配布・更新対応・検証を続けるため、r-fallingstarへの任意の支援を受け付けています。

[GitHub SponsorsでこのForkの保守を支援する](https://github.com/sponsors/r-fallingstar)

支援はこの非公式Forkの保守に充てます。個別サポートや機能追加をお約束するものではありません。
