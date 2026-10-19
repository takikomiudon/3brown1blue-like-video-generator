# 制作ノウハウの索引

ここから、会話で扱った調査・設計・実装・検証・保存の知識をたどれる。
2026-10-18に、会話履歴と公開元から復元してGitに保存した。

|知りたいこと|文書・実装|
|---|---|
|アイデアから動画出力までの工程と先行事例|[research.md](research.md)|
|今回の科学的な主張、仮定、模式図の境界|[fact-check.md](fact-check.md)|
|音声・素材のクレジット|[credits.md](credits.md)|
|完成までのコマンドと段階的確認|[production-workflow.md](production-workflow.md)|
|最初の4分動画の構成・記録|[storyboard.md](storyboard.md)、[validation.md](validation.md)|
|「1→100」を目指す既存技術の調査・採用順位|[quality-upgrade.md](quality-upgrade.md)|
|中性子の収支を使う比較試作の設計|[quality-upgrade-pilot.md](quality-upgrade-pilot.md)|
|教養ショートのテーマ選びと、その提案への指摘|[shorts-topic-research.md](shorts-topic-research.md)|
|尺と収益化についての回答の範囲|[platform-duration-notes.md](platform-duration-notes.md)|
|実際に制作した65秒ショート|[README](../shorts/decay-heat/README.md)、[演出計画](../shorts/decay-heat/plan.md)|
|PageIndexのショート：ツリーによる資料探索|[README](../shorts/pageindex/README.md)、[演出計画](../shorts/pageindex/plan.md)、[出典](../shorts/pageindex/sources.md)|
|RAG動向の日本語ショート10本：論文と実装|[動画・台本一覧](../shorts/rag-trends-2026/README.md)、[制作計画](../shorts/rag-trends-2026/plan.md)、[出典と確認事項](../shorts/rag-trends-2026/research-notes.md)|
|Docker、音声、文字、尺、リンク切れの対処|[troubleshooting.md](troubleshooting.md)|
|説明対象の動作を設計し、完成映像で確認する|[動作契約](../.agents/skills/science-explainer/references/motion-contract.md)|
|VOICEVOXで日本語音声を生成・同期・検証する|[音声の制作条件](../.agents/skills/science-explainer/references/voicevox.md)|
|同じ原稿で10話者を聴き比べる|[音声比較と個別MP3](../audio-comparisons/voicevox-10/README.md)|
|制作スキルv2.0.0の変更と検証|[改訂記録](animation-contract-v2.md)、[検証結果](animation-contract-v2-validation.json)|
|Gitへの保存・ユーザーへの受け渡し|[preservation-and-delivery.md](preservation-and-delivery.md)|
|何をどの根拠で復元したか|[restoration.md](restoration.md)|
|スキルの固定コミット・ライセンス・ハッシュ|[vendor-skills.json](vendor-skills.json)|
|研究で参照したリポジトリ|[quality-upgrade-source-links.md](quality-upgrade-source-links.md)、[sources.json](sources.json)|

## エージェント用スキル

|スキル|役割|由来|
|---|---|---|
|[science-explainer](../.agents/skills/science-explainer/SKILL.md)|このプロジェクトの制作・検証・受け渡し|会話から復元し再発防止を追記|
|[manim-video](../.agents/skills/manim-video/SKILL.md)|演出仕様、Manim制作、画像による見直し|ApliroAI/manim-video-lab|
|[manim-composer](../.agents/skills/manim-composer/SKILL.md)|問い・構成・場面設計|adithya-s-k/manim_skill|
|[manimce-best-practices](../.agents/skills/manimce-best-practices/SKILL.md)|Manim Communityの実装|adithya-s-k/manim_skill|
|[remotion-best-practices](../.agents/skills/remotion-best-practices/SKILL.md)|Reactでの動画・字幕・タイミング|remotion-dev/skills|

現在のショートはManim CommunityとVOICEVOX。Remotion、ManimGL、Manim Voiceoverプラグインを実行に使ったわけではない。
スキルの導入と、対応ランタイムの導入・動作検証を混同しない。

## 検証する

```bash
python3 scripts/verify_knowledge.py
```

索引のリンク、必要な文書、スキルの原本とのハッシュ、完成動画のハッシュ等を確認する。
この検証は、動画を新規レンダリングしたり全編を人が視聴したりするものではない。
