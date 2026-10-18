# 出典と事実確認

確認日：2026-10-18。対象：VectifyAIのPageIndex。
公式GitHubリポジトリを取得し、以下の固定コミットを実際に確認した。

- [公式README](https://github.com/VectifyAI/PageIndex/blob/e7d1cc67e4dd5bfe4cac63b161b313ef41328705/README.md)：tree-structure index、LLM reasoningによるretrieve、vectorless、ページへの参照、ローカル版とCloudの差。
- [Flash README](https://github.com/VectifyAI/PageIndex/blob/e7d1cc67e4dd5bfe4cac63b161b313ef41328705/pageindex/flash/README.md)：構造はPDFレイアウトから生成、summaryと最適化はLLMを利用。ノードにtitle/node_id/start_index/end_index/summary/nodes。
- [agent_tools.py](https://github.com/VectifyAI/PageIndex/blob/e7d1cc67e4dd5bfe4cac63b161b313ef41328705/pageindex/agent_tools.py)：get_document_structureで章と要約を取得し、get_page_contentで本文を得る仕組み。該当関数周辺を確認。

## 動画内の主張

|主張|根拠・範囲|
|---|---|
|代表的なRAGは文章を分けて類似度で探す|公式比較表でvector RAGの代表例として紹介されている方式。RAGには他の方式や再ランキング、ハイブリッドもあり、全RAGを指さない。|
|PageIndexは構造をたどる|公式のIndex→Retrieveの説明と章要約を使う探索。アニメーションの一本の経路は理解用の簡略化であり、必ず一方向だけ進む実装だとはしていない。|
|ベクトルDBを使わない|公式のvectorlessという特徴。LLMの内部表現までベクトルを使わないという意味ではない。|
|根拠ページを参照して回答する|READMEのtraceable、localのpage-level citations、および本文取得ツール。引用や回答が必ず正しいという保証ではない。|
|精度・時間・費用を検証する必要がある|索引・検索のLLM利用、モデル依存のコストと精度を扱う公式の説明を踏まえた運用上の判断。新しいベンチマークを実施したわけではない。|

## 架空の例

「決算資料」「経営方針p.8」「業績」「費用の分析p.42」「物流費増加による利益減少」は新規に作った架空の説明例。
実在する企業・報告書・実測結果ではない。一般的な検索が必ずこの誤答を選ぶという再現実験でもない。
動画内にも「架空の資料／仕組みの模式図」を表示する。
公式ベンチマークの98.7%等の数値は、条件を省いて一般化しないため動画に入れない。
図と文章は本プロジェクトの新規制作。公式ロゴ、スクリーンショット、販促画像は使っていない。
