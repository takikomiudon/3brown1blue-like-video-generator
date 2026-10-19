# 制作から受け渡しまでの実行手順

現行の実装例は `shorts/decay-heat/`。既存の完成動画を渡すだけなら、音声エンジンやレンダラーを起動する必要はない。

## 0. 既存の保存物を確認する

```bash
git status --short
git branch --show-current
git log -3 --oneline
python3 scripts/verify_knowledge.py
```

成果・ノウハウ・スキルは `main` に統合済み。既存チェックアウトのmainで作業する。
利用者の変更を残したまま進め、checkoutやresetで消さない。

## 1. 出典と企画

- 新作は [science-explainerの動作契約](../.agents/skills/science-explainer/references/motion-contract.md) を適用する。`motion-plan.json` に対象の状態変化と、その変化が伝える関係を記述する。
- 中心部分の5〜10秒を実際に描画し、中間状態と意味の対応を確認してから全編へ展開する。
- [科学的確認](fact-check.md)と[テーマ選び](shorts-topic-research.md)を読む。
- 対象、中心の理解、視聴者の関心の根拠を一文ずつ決める。
- Manim Video Lab等の既存手順を使い、図・対象・色・注目・台詞・動き・保持時間を `plan.md` に書く。
- 一つの代表的な短い区間を試してから、全編へ展開する。

## 2. 原稿と音声

`story.json` の `say` は全文の読み上げ、`caption` は画面上の短い要約。
専門語、英字、数値の読みを確認。改行や字幕の省略で科学的な条件を落とさない。

日本語ナレーションはVOICEVOXで合成する。標準話者は、ユーザーが比較後に選択した冥鳴ひまり・ノーマル。
ユーザーが別の音声構成を指定した場合はその指定を優先する。
詳細は [VOICEVOXの制作条件](../.agents/skills/science-explainer/references/voicevox.md)。

エンジンの起動：

```bash
cd shorts/decay-heat
docker run -d --name decay-heat-voicevox \
  -p 127.0.0.1:50021:50021 --cpus 2 \
  voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90
```

`/version` が応答してから `python3 prepare_audio.py`。
この実装は12区間を合成し、48kHz WAV、クエリ、実測タイムライン、全文SRTを作る。
話速1.04、pitchScale -0.015、音声前後の余白等を設定。各区間の尺に0.85秒の余裕を加え、30fps単位へ切り上げる。最後に2.5秒の保持。
原稿・設定のSHA-256が違う場合は既存音声を再利用しない。

音声のクレジットは動画末尾と投稿文に記載。話者の利用条件を `speaker_info` から保存する。
音声作成後に自分が起動したエンジンだけを停止・削除すると、Dockerのディスク使用量を抑えられる。

## 3. 描画環境

Manim Community 0.20.1、Pythonを含む公式イメージを固定。日本語フォントはホストから読み取り専用で渡す。
ManimGLとは別物。ホストのCairo/Pango開発ヘッダーがないために失敗する場合は、実績のあるコンテナを使う。

```bash
BUILDX_CONFIG=/tmp/decay-heat-buildx docker build \
  --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt \
  -t decay-heat-manim:0.20.1 .
```

管理環境ではプロキシとCAを保持する。CAはBuildKit secretとして渡し、セッションの証明書をイメージへCOPYしない。
`.docker/buildx` が読み取り専用なら `BUILDX_CONFIG` だけを書ける場所へ向ける。`DOCKER_CONFIG` や認証を置き換えない。

公式VOICEVOX CPUイメージには大きなレイヤーがあり、以前の動画の再制作時は取得に約16分かかった。別環境・ネットワークで同じ時間になるとは限らない。
ダイジェストを固定し、既存イメージを使う。完成動画の再配布に、この再取得は不要。

## 4. 試写と同期

```bash
bash run.sh manim -ql -r 540,960 --fps 30 --disable_caching script.py DecayHeatShort
```

現在のコードは固定カメラの一つのScene。対象の拡大・縮小で原子炉→燃料→原子核→原子炉へつなぐ。
短い台詞の実測尺と `add_sound` で同期し、重要な箇所はVOICEVOXのモーラ時間から位置を決める。
具体例は `wait_for_kana('オシマス')` と `wait_for_kana('ホオカイネツ')`。
Manim VoiceoverやWhisperXによる全語アラインメントを実行したという意味ではない。

キーフレームは、冒頭、各密な説明、切り替え途中、グラフ、冷却喪失、最後の結論を含める。
試写では縮小原子炉の透明度とグラフの重なりを修正し、原子核を拡大した。

## 5. 完成出力と検証

```bash
bash run.sh manim -qh -r 1080,1920 --fps 30 --disable_caching script.py DecayHeatShort
bash run.sh python finalize.py
```

`finalize.py` は以下を実施する。

- 音量を二段階のloudnormで調整。目標I=-16、TP=-1.5、LRA=11。
- 1080pは描画した映像ストリームをコピーし、音声をAAC化。faststartを付ける。
- 音声の末尾に必要な無音を足す。Manimの丸めで増えた最終保持の1フレームを契約尺へそろえる。音声や説明部分を切って尺を合わせない。
- 720p/1280の軽量版をH.264 Main、level 3.1、yuv420p、AACで作る。
- ffprobeで解像度・形式・fps・尺・フレーム数・音声の長さを確認。
- 最終MP4を全編デコードしてエラーを検出。音声ピーク、サイズ、SHA-256、静止画を保存。

数値のピーク、LUFS、true peakは同一指標ではない。検査した指標をその名前で報告する。
静止画の見直しを、人による全編の動画・音声の視聴と表現しない。

## 6. 保存して渡す

新作の完成判定には、最終MP4の主図に対する動作検査と、そのSHA-256に結びついた意味のレビューが必要。
動作契約のコマンドで `status: PASS` を確認し、計画・レビュー・検査結果をコードとともに保存する。
この手順の追加により、過去の出力が新しい検査を実施済みになるわけではない。

[保存と受け渡し](preservation-and-delivery.md)の手順で、GitHubへ保存してからURLを再取得する。
既存の出力が有効なら新たにレンダリングしない。ライブプロセスの存続や、未コミットのファイルの残存に依存しない。
