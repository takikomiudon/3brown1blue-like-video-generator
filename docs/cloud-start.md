# クラウド環境の起動手順

既存の `/workspace/3brown1blue-like-video-generator` を使う。worktreeは利用者が明示的に依頼した場合だけ作る。
作業開始時に `git status --short`、ブランチとHEADを確認する。
変更のないチェックアウトでは `bash scripts/bootstrap_knowledge.sh` を実行し、存在する文書の版にかかわらず、originのmainを取得してfast-forwardで更新する。
ローカル変更や分岐した履歴は保存し、自動更新が止まった理由を調べる。resetや変更の破棄は行わない。
本書・AGENTS.md・docs/KNOWLEDGE.md・science-explainer/SKILL.mdを読む。

音声は利用者が選択した **VOICEVOX:冥鳴ひまり・ノーマル**。
スキルの `voice-defaults.json` を読み込む `scripts/voicevox_audio.py` を使い、実エンジンの名前・UUID・スタイルを照合する。
音声生成前に使ったHEADと設定のSHA-256を記録する。
新作・再生成の受け渡しでは、最終MP4に結びついた生成記録と現在の話者指定を照合する。
既存動画を求められた場合は、その動画の実際の話者と制作時点を説明する。

知識確認にはPython標準ライブラリを使う。制作時はDocker・ffmpeg/ffprobe・Noto Sans CJKを確認し、
`docs/production-workflow.md` とスキルのVOICEVOX手順に従って必要なサービスを起動する。
管理環境のruntimeスキルを読み、既存のプロキシ・CAと固定イメージを使う。
VOICEVOXの `/version`・`/speakers` が応答してから合成を開始する。自分が起動したエンジンは合成後に停止する。
mainへ保存・pushし、確定コミットのHTTPSから成果物を再取得してハッシュを照合する。

## 設定の保存と適用

環境設定の `install_script` には [bootstrap_knowledge.sh](../scripts/bootstrap_knowledge.sh) の全内容を保存する。
`start_skill` には本書の起動手順を保存する。依存関係が保存されても、サービスのプロセスが次の環境で動いているとは仮定しない。
設定の下書き、公開された環境の版、現在のチェックアウトをそれぞれ確認する。
下書きの保存は環境の公開ではなく、公開前の別セッションに反映済みとは報告しない。
