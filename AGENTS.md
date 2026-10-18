# このリポジトリで作業するエージェントへ

## 最初に読むもの

1. [README.md](README.md)
2. [ノウハウの索引](docs/KNOWLEDGE.md)
3. 制作なら [.agents/skills/science-explainer/SKILL.md](.agents/skills/science-explainer/SKILL.md)
4. 縦型動画なら [shorts/decay-heat/README.md](shorts/decay-heat/README.md) と [演出計画](shorts/decay-heat/plan.md)

## 利用者の指示から確定した方針

- 新しい方法を独自に考案する前に、実作例・公式資料・既存のエージェント用スキルを調べて使う。
- 3Blue1Brownのように、図や対象の変化を追って直感的に理解できる科学解説を目指す。
- 原稿、出典、音声設定、動き、検証、受け渡しまで再生成可能な形で保存する。
- テーマに「なぜ？」を付けただけで、視聴者に関心があると仮定しない。実際の興味の根拠と、制作側が考えた仮説を分ける。
- 「バズる」「100倍の品質」等を、検証なしに達成済み・実証済みと表現しない。

## 消失を繰り返さないための保存

- 作業環境のファイル、Gitのコミット、GitHubへのpush、環境設定の下書き、公開済みスナップショットは別物。
- 完了前に `git status` と保存対象を確認する。コード・README・SKILL・参照資料・必要な成果物をコミットし、許可された作業ブランチへpushする。
- 現在の成果とノウハウは **`video/decay-heat-delivery`** ブランチにある。`main` は初期READMEだけの場合がある。
- ファイルがない場合、まず作業ディレクトリ、ブランチ、`git log`、`git ls-remote origin refs/heads/video/decay-heat-delivery` を確認する。元ファイルの取得より先に再生成を始めない。
- 新しい環境では既存のチェックアウトを使う。明示的依頼なしにworktreeを作らない。利用者の変更をreset・上書きしない。
- このクラウドの `/workspace/...` パスだけを、ユーザーが受け取れる動画リンクとして提示しない。GitHubの確定コミットにあるMP4のHTTPS URLを使い、実際に再取得してSHA-256を比較する。
- 未公開のファイルを別サービスへ勝手に公開しない。このリポジトリへの保存も、ユーザーの承認済みの作業範囲に従う。

## 実装・検証

- 新作は `science-explainer` v2.0.0の動作契約を適用する。説明対象の状態変化と、その変化が伝える意味を設計し、5〜10秒の試作が合格してから全編へ進む。
- 完成判定には、最終MP4の主図に対する `audit_motion.py` の検査と、同じSHA-256に結びつく意味のレビューの両方を必須とする。コマンドと書式は [.agents/skills/science-explainer/references/motion-contract.md](.agents/skills/science-explainer/references/motion-contract.md)。
- 現行ショートはManim Community、VOICEVOX。RemotionとManimGLのAPIを混在させない。
- 台本の編集元は各動画の `story.json`。音声の尺を測ってタイムラインを作る。
- 既存成果物を渡すだけなら再レンダーは不要。リポジトリ内のMP4と検証記録を先に使う。
- 文書・スキルを変更したら `python3 scripts/verify_knowledge.py`。動画の生成手順と検証は [制作手順](docs/production-workflow.md)。
- ベンダー化したスキルを直接修正しない。調整はプロジェクト固有スキルで行い、上流のコミット・ライセンス・SHA-256を保持する。
- ネットワークやDockerは管理環境のプロキシ・CAを使い、TLS・署名・チェックサムを無効化しない。
- secretの値、環境変数の全ダンプ、認証ファイルをログや文書に残さない。
- passed / failed / 未実施 / 過去の実行記録を区別する。静止画の確認を、全編の動画・音声の視聴と表現しない。
