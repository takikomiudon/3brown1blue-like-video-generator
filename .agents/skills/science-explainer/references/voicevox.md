# VOICEVOXによる日本語ナレーション

日本語ナレーションはVOICEVOXで合成する。ユーザーが10話者の比較後に選択した **冥鳴ひまり・ノーマル** を標準話者として固定する。
設定は [voice-defaults.json](../voice-defaults.json)。
ユーザーが音声構成や話者を指定した場合は、その明示的な指定を優先する。
描画にManimとRemotionのどちらを使う場合も、この音声条件を適用する。

## エンジンと話者の準備

既存のVOICEVOX ENGINEがあれば `/version` と `/speakers` の応答を確認する。
新しく準備する場合は、管理環境のプロキシ・CA・Dockerの手順を守って起動する。
このリポジトリで実行済みのCPUイメージは以下の0.25.2版。

```bash
docker run -d --name explainer-voicevox \
  -p 127.0.0.1:50021:50021 --cpus 2 \
  voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90
```

起動済みの同名コンテナやポートの利用状況を先に確認する。
起動コマンドの終了だけで準備完了とせず、APIの応答を待つ。
`/speakers` の話者名「冥鳴ひまり」とスタイル名「ノーマル」を照合し、そのエンジンでのstyle idを決める。
VOICEVOX ENGINE 0.25.2ではstyle id 14、speaker UUIDは `8eaad775-3119-417e-8cf4-2a10bfd592c8`。
APIキーは不要。ローカルAPIへの接続は127.0.0.1を使う。

## 合成と同期

1. `story.json` 等の編集元から、読み上げ用の原稿を用意する。
2. `POST /audio_query?text=...&speaker=...` でクエリを得る。
3. 話速・ピッチ・音量・前後の余白・サンプルレートを設定する。
4. `POST /synthesis?speaker=...` にクエリJSONを渡し、WAVを保存する。
5. WAVの実測秒数からタイムラインを作り、語句や文の位置へ動作を同期する。
6. 専門語の発音、語頭・語尾、文間、速度と音量を確認し、必要な区間を再合成する。

音声生成には、設定を直接読み込む共通実装 [voicevox_audio.py](../scripts/voicevox_audio.py) を使う。
新規プロジェクトでも、スキルフォルダ全体を設置して次を実行する。

```bash
python3 /path/to/science-explainer/scripts/voicevox_audio.py /path/to/project
python3 /path/to/science-explainer/scripts/voicevox_audio.py /path/to/project --check
```

プロジェクトに `story.json`（各項目に `id` と `say`）を用意する。
共通実装は話者名・UUID・スタイル名を `/speakers` と照合し、現在のIDで合成する。
選択した話者を利用できる状態でのみ生成を進める。
既存の [prepare_audio.py](../../../../shorts/pageindex/prepare_audio.py) とRAGシリーズの `prepare.py --audio` も、この共通実装を呼ぶ。
話速1.04、pitchScale -0.015、48kHz、前0.12秒・後0.14秒の設定を使っている。
これらは既存作品の設定例であり、題材や台詞に応じて読みやすく調整する。
発音用原稿と画面の通常表記はそれぞれ管理できる。

原稿・話者・全合成設定・エンジン版・WAVとクエリのSHA-256が一致する場合だけ、既存WAVを再利用する。
生成後の `assets/voice.json` と台本・タイムライン・音声の照合を `--check` で行う。
映像のクレジットは、この検証を通った生成記録の `credit` を使う。
Manimの描画後は共通実装の `save_render` で入力と動画のハッシュを保存し、最終出力の前に `verify_render` で照合する。
描画コンテナからは、スキルフォルダを読み取り専用でマウントして `SCIENCE_EXPLAINER_SKILL` に設置先を指定する。
同梱の `run.sh` と `run_batch.py` はこのマウントを行う。
ユーザーが別の話者を明示した場合は、その指示に合わせて `voice-defaults.json` の話者名・UUID・スタイル・クレジットを更新してから生成する。
起動や合成の問題はログとAPI応答で診断して復旧する。
実行が阻害されている場合は、完了した工程と阻害要因を明示する。
音声構成の変更はユーザーの明示的な指定に従う。

## 生成記録とクレジット

`assets/voice.json` にエンジン名・版、話者名、スタイル名・id、合成設定、クレジットを保存する。
各原稿のクエリJSONと、合成したWAVのSHA-256も保存する。
`speaker_info` から取得した利用条件を保存し、動画と投稿文に実際の話者のクレジットを記載する。
標準話者のクレジットは **音声：VOICEVOX:冥鳴ひまり**。話者を指定変更した場合は実際の話者名を使う。

## 完成MP4の確認

- 音声トラックをMP4へ収録し、ffprobeで音声ストリームが存在して正の長さを持つことを確認する。
- 最終MP4を全編デコードし、音量と音声・映像の尺を検査する。
- 各区間の発音と語頭・語尾、映像との同期を確認する。
- 生成記録の話者と、動画・投稿文のクレジットが一致していることを確認する。
- 実際に確認した方法と範囲を検証記録に残す。

ffprobeは音声形式と尺の検査に使う。VOICEVOXでの生成の確認には、合成クエリとエンジン・話者の記録を使う。
自分が起動したエンジンは合成後に停止し、ユーザーの他のプロセスは維持する。

## 話者を比較する場合

同じ原稿・話速・ピッチ・抑揚・前後の余白で合成し、出力の音量も共通の基準に揃える。
個別音声と、番号・名前を読み上げる比較音声を用意すると選びやすい。
人気順を扱う場合は指標と出典を確認し、確認できたランキングと比較用の候補選定を区別する。
実装例は [10話者の音声比較](../../../../audio-comparisons/voicevox-10/README.md)。

## 設定の回帰確認

```bash
python3 -m unittest discover -s .agents/skills/science-explainer/scripts -p test_voicevox_audio.py
python3 scripts/verify_knowledge.py
```

v2.0.4では、3つの制作入口による実エンジン合成と、各Manimクラスの描画処理を継承した短い検証シーンを確認した。
話者選択、旧キャッシュの更新、入力と描画結果の照合を検査する。
[実行結果と確認範囲](../../../../docs/voice-default-validation.json)を参照。音声の聴取と全編の再制作は別の確認工程として記録する。
