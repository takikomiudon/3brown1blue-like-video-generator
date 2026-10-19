# 3brown1blue-like-video-generator

制作ノウハウは **[docs/KNOWLEDGE.md](docs/KNOWLEDGE.md)** にまとめています。
調査、テーマ設定、科学的な確認、演出、音声、レンダリング、検証、受け渡しの手順と、
5つの[エージェント用スキル](.agents/skills)を保存しています。
復元の根拠と範囲は [復元記録](docs/restoration.md) を参照してください。

成果・ノウハウ・スキルは `main` に統合済みです。新しい環境でも `main` を使ってください。
取得後は `python3 scripts/verify_knowledge.py` で整合性を確認できます。

## 制作スキルの呼び出し

```text
$science-explainer を使って、〇〇の仕組みを日本語ショート動画にして。
```

[science-explainer v2.0.3](.agents/skills/science-explainer/SKILL.md) は、説明対象の状態変化を通して理解できるアニメーションを制作します。
日本語ナレーションはVOICEVOXで制作し、ユーザーが選択した **冥鳴ひまり・ノーマル** を標準話者として使います。
動く試作、最終映像の主図の検査、対象の変化と意味のレビューを必須としています。
別の環境へ導入するときは、フォルダ全体と必要な兄弟スキルを取得してください。
以前コピーした版や以前のコミットへのリンクは自動更新されないので、読み込むSKILL.mdの `metadata.version` を確認します。

## VOICEVOXの話者を比較する

- [10話者を続けて聴く（MP3）](audio-comparisons/voicevox-10/outputs/voicevox-10-comparison.mp3)
- [個別音声をまとめて取得（ZIP）](audio-comparisons/voicevox-10/outputs/voicevox-10-audio.zip)
- [話者一覧・共通原稿・条件](audio-comparisons/voicevox-10/README.md)

## PageIndex：目次をたどって、根拠に届く

日本語ナレーション・字幕付きの約65秒の縦型動画。

- [完成動画（1080p）](shorts/pageindex/outputs/pageindex-short-ja.mp4)
- [軽量版（720p）](shorts/pageindex/outputs/pageindex-short-ja-720p.mp4)
- [台本・出典・再生成手順](shorts/pageindex/README.md)

## 原子炉を止めても、なぜ冷却が必要？

日本語ナレーション・字幕付きの約65秒の縦型動画。

- [完成動画（1080p）](shorts/decay-heat/outputs/decay-heat-short-ja.mp4)
- [軽量版（720p）](shorts/decay-heat/outputs/decay-heat-short-ja-720p.mp4)
- [原稿・再生成手順・クレジット](shorts/decay-heat/README.md)

GitHubの動画ファイルページで **Download raw file** を選ぶとダウンロードできます。
音声：VOICEVOX:青山龍星。
