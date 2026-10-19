# 読む論文と知っておきたい実装

年はarXiv初回公開年。基礎論文を読み、その後の公式実装の更新状況と分けて確認する。確認日：2026年10月19日。

|テーマ|論文|初回公開|
|---|---|---|
|GraphRAG|[From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130)|2024|
|LightRAG|[LightRAG: Simple and Fast Retrieval-Augmented Generation](https://arxiv.org/abs/2410.05779)|2024|
|KAG|[KAG: Boosting LLMs in Professional Domains via Knowledge Augmented Generation](https://arxiv.org/abs/2409.13731)|2024|
|RAPTOR|[RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval](https://arxiv.org/abs/2401.18059)|2024|
|Self-RAG|[Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511)|2023|
|CRAG|[Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884)|2024|
|BGE-M3|[M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation](https://arxiv.org/abs/2402.03216)|2024|
|ColPali|[ColPali: Efficient Document Retrieval with Vision Language Models](https://arxiv.org/abs/2407.01449)|2024|
|Agentic-R|[Agentic-R: Learning to Retrieve for Agentic Search](https://arxiv.org/abs/2601.11888)|2026|
|MTRAG-UN|[MTRAG-UN: A Benchmark for Open Challenges in Multi-Turn RAG Conversations](https://arxiv.org/abs/2602.23184)|2026|

実装の入口は各動画のsources.mdに記載。追加で押さえる役割：

- FlagEmbedding：埋め込みモデルとリランカー。
- Docling：PDF等の構造を扱う取り込み・変換。
- Ragas：検索と回答の評価。
- LlamaIndex：データの取り込み・索引・問い合わせ。
- Haystack：部品をパイプラインとして接続。
- LangGraph：状態、分岐、繰り返し、再開を持つ処理の制御。

これらの役割には重なりがある。公式ガイドと自分の資料での検証をもとに選ぶ。
