# RAGの現在地：10本のショート動画

2026年10月19日確認。日本語・1080×1920・24fps。音声と焼き込み字幕付き。
基礎論文と2026年の研究・実装状況を区別して解説します。
対象：RAGの基礎を知る初中級エンジニア。図は説明用の模式図です。

[10本・台本・字幕を一括ダウンロード](rag-trends-10-videos.zip)

|#|動画|時間|台本・一次資料|
|---|---|---|---|
|1|[GraphRAG](01_graphrag/outputs/final.mp4)|60.8秒|[台本と出典](01_graphrag/script.md)|
|2|[LightRAG](02_lightrag/outputs/final.mp4)|58.8秒|[台本と出典](02_lightrag/script.md)|
|3|[KAG](03_kag/outputs/final.mp4)|55.9秒|[台本と出典](03_kag/script.md)|
|4|[RAPTOR](04_raptor/outputs/final.mp4)|55.8秒|[台本と出典](04_raptor/script.md)|
|5|[Self-RAG × CRAG](05_selfrag_crag/outputs/final.mp4)|56.2秒|[台本と出典](05_selfrag_crag/script.md)|
|6|[検索 × Rerank](06_hybrid_rerank/outputs/final.mp4)|56.0秒|[台本と出典](06_hybrid_rerank/script.md)|
|7|[ColPali × Docling](07_multimodal/outputs/final.mp4)|53.2秒|[台本と出典](07_multimodal/script.md)|
|8|[Agentic-R](08_agentic_r/outputs/final.mp4)|60.1秒|[台本と出典](08_agentic_r/script.md)|
|9|[MTRAG-UN × Ragas](09_mtrag_ragas/outputs/final.mp4)|58.7秒|[台本と出典](09_mtrag_ragas/script.md)|
|10|[RAG実装の選び方](10_libraries/outputs/final.mp4)|57.1秒|[台本と出典](10_libraries/script.md)|

各回は問い・仕組み・使いどころ・注意点・読む資料の5区間です。
論文の主張や実験条件の詳細は、各回の台本から一次資料へ進んでください。

**音声：VOICEVOX:青山龍星**（ノーマル、ENGINE 0.25.2）。投稿時は付属のdescription.txtのクレジットを記載してください。

検証：全MP4の全編デコード、映像と音声の形式・尺、音量、字幕範囲、主図の動作検査、同じSHA-256に対応する連続フレームの意味レビューを実施。
字幕は実測発話内の文字数配分による推定タイミングです。人による全編の音声聴取は未実施で、機械検査・クエリ確認と区別しています。

編集元はepisodes.jsonと各回のstory.json。合成クエリと音声設定を保存しています。
[論文・ライブラリの読むリスト](reading-list.md) / [編集時の確認事項](research-notes.md) / [制作計画](plan.md) / [全出典](sources.json) / [納品ファイルのハッシュ](manifest.json)

## 再生成

掲載済み動画の音声記録は制作時のものです。これからの再生成では、共通の
[話者設定](../../.agents/skills/science-explainer/voice-defaults.json)にある冥鳴ひまり・ノーマルを使います。
音声からタイムライン・映像を再生成して、クレジットと検証記録を更新します。

DockerとホストのNoto Sans CJKフォントを使用。既存のdecay-heat-manim:0.20.1がない場合は同梱Dockerfileから作成します。
初回の描画前に、pilot/review.jsonおよび各回のpilotレビューと対応する試作動画を参照してください。

```bash
BUILDX_CONFIG=/tmp/rag-buildx docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t decay-heat-manim:0.20.1 .
docker run -d --name rag-trends-voicevox -p 127.0.0.1:50021:50021 --cpus 3 voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90
# /version が応答した後に実行
python prepare.py --audio
python run_batch.py --workers 2
docker stop rag-trends-voicevox
```

再生成後は新しい最終MP4をレビューし、そのSHA-256に対応するmotion-review.jsonでaudit_motion.pyを実行してください。過去のレビューを新しい動画に流用しないでください。
