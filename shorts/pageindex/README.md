# PageIndex：目次をたどって、根拠に届く

約65秒、日本語ナレーション・字幕付き、9:16のショート動画。
PageIndexの公式資料を確認し、架空の決算資料で検索の仕組みを新規作図した。

- [完成動画（1080p）](outputs/pageindex-short-ja.mp4)
- [軽量版（720p）](outputs/pageindex-short-ja-720p.mp4)
- [全文字幕](outputs/pageindex-ja.srt)
- [台本](story.json) / [演出計画](plan.md) / [出典と主張の範囲](sources.md)
- [機械的な検証結果](outputs/validation.json)
- [画面・発音・形式の確認記録](review.md)

GitHubで再生されない場合は、MP4のファイルページの **Download raw file** から保存してください。

## 内容

「利益が減った理由」を知りたいとき、単に「利益を増やす目標」が見つかっても答えにはならない。
PageIndexは文書を章・節のツリーに整理し、AIが読む場所を選ぶ。
動画は決算資料→業績→費用の分析→p.42の本文→根拠付き回答という関係を見せる。
代表的なベクトル検索との発想の違いを模式化したもので、実製品の実行デモ・比較実験ではない。
精度、時間、コストの優位性は断定していない。

## 再生成

リポジトリの [制作手順](../../docs/production-workflow.md) と同じ、
Manim Community 0.20.1 / VOICEVOX ENGINE 0.25.2を使用。
このディレクトリから実行する。Docker、ホストのNoto Sans CJK、管理環境のプロキシ・CAを使う。

```bash
BUILDX_CONFIG=/tmp/pageindex-buildx docker build \
  --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt \
  -t decay-heat-manim:0.20.1 .
docker run -d --name pageindex-voicevox \
  -p 127.0.0.1:50021:50021 --cpus 2 \
  voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90
# /version の応答を確認してから音声を作る。
python3 prepare_audio.py
docker stop pageindex-voicevox
docker rm pageindex-voicevox
bash run.sh manim -ql -r 540,960 --fps 30 --disable_caching script.py PageIndexShort
# 試写・図の確認後に完成版を出力。
bash run.sh manim -qh -r 1080,1920 --fps 30 --disable_caching script.py PageIndexShort
bash run.sh python finalize.py
```

`decay-heat-manim:0.20.1` は前作から共用する描画環境名で、動画の内容は新規の `script.py`。
完成MP4、台本、コード、出典、音声クエリ、実測タイムライン、音声の利用条件をGitに保存する。
WAVと描画キャッシュは再生成可能な中間ファイルとしてGit管理から除外している。
`story.json` の `say` は発音用。章・節を「しょう・せつ」、RAGを「ラグ」と指定して誤読を防ぐ。

**音声：VOICEVOX:青山龍星**。公開時は投稿文にも記載する。
取得した話者の利用条件は [voice-policy.md](assets/voice-policy.md)。
図・文章は本プロジェクトの新規制作で、PageIndexの公式動画ではない。
