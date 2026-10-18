# VOICEVOX 10話者の聴き比べ

同じ原稿を10名のノーマル音声で合成しました。比較番号は人気順位ではありません。

- [名前の読み上げ付き・連続比較（約2分17秒、MP3）](outputs/voicevox-10-comparison.mp3)
- [個別10音声＋比較版をまとめてダウンロード（ZIP）](outputs/voicevox-10-audio.zip)
- [再生順リスト](outputs/playlist.m3u) / [検証結果](outputs/validation.json)

MP3がブラウザで再生されない場合は、GitHubのファイルページで **Download raw file** を選んで保存してください。

## 個別音声

|比較番号|話者|比較版の開始目安|共通原稿のみの音声|
|---|---|---|---|
|01|ずんだもん|00:00|[MP3](outputs/01-zundamon.mp3)|
|02|四国めたん|00:14|[MP3](outputs/02-shikoku-metan.mp3)|
|03|春日部つむぎ|00:27|[MP3](outputs/03-kasukabe-tsumugi.mp3)|
|04|WhiteCUL|00:40|[MP3](outputs/04-whitecul.mp3)|
|05|冥鳴ひまり|00:53|[MP3](outputs/05-meimei-himari.mp3)|
|06|ナースロボ＿タイプＴ|01:07|[MP3](outputs/06-nurse-robot-type-t.mp3)|
|07|中国うさぎ|01:21|[MP3](outputs/07-chugoku-usagi.mp3)|
|08|雨晴はう|01:37|[MP3](outputs/08-amehare-hau.mp3)|
|09|波音リツ|01:50|[MP3](outputs/09-namine-ritsu.mp3)|
|10|青山龍星|02:03|[MP3](outputs/10-aoyama-ryusei.mp3)|

## 共通原稿と条件

> ページインデックスは、資料を章や節のツリーに整理します。AIが読む場所を選び、根拠のページを確認して回答します。

全員ノーマル、話速1.0、ピッチ0、抑揚1.0。48kHz・モノラルで合成しました。
同じ二段階のloudnormでI=-16 LUFS / TP=-1.5 dBTP / LRA=11を目標に調整してからMP3化しています。
比較版には各話者による番号・名前の読み上げと区切りの間があります。個別ファイルの原稿は全員共通です。
話者ごとの自然なテンポを保っているため、共通原稿の読み上げ時間には差があります。

## 候補の選び方

確認日：2026-10-19。VOICEVOX ENGINE 0.25.2の話者・スタイルを実際に取得して確認しました。
人気上位10名を裏づける統計は今回確認できなかったため、定番として知られる候補を比較対象にしています。
比較番号は順位を意味せず、今回の候補一覧を人気ランキングとして再利用しないでください。
公式サイトの本文はこの環境から取得できず、GitHubの公開検索でも順位の根拠を確認できませんでした。

## 音声クレジット

- VOICEVOX:ずんだもん
- VOICEVOX:四国めたん
- VOICEVOX:春日部つむぎ
- VOICEVOX:WhiteCUL
- VOICEVOX:冥鳴ひまり
- VOICEVOX:ナースロボ＿タイプＴ
- VOICEVOX:中国うさぎ
- VOICEVOX:雨晴はう
- VOICEVOX:波音リツ
- VOICEVOX:青山龍星

エンジンから取得した各話者の利用条件は `assets/*.policy.md` に保存しています。
音声を再公開するときは、実際に使用する話者の利用条件とクレジットを引き継いでください。

## 再生成

ローカルのVOICEVOX ENGINEを127.0.0.1:50021で起動し、このリポジトリの[音声の制作条件](../../.agents/skills/science-explainer/references/voicevox.md)に従います。
Python標準ライブラリ、ffmpeg、ffprobeを使用します。

```bash
python3 generate.py
```

`config.json` が原稿・話者・設定、`generate.py` が合成・音量調整・結合・検証・ZIP作成を行います。
クエリ、実測尺、設定、WAVとMP3のSHA-256を保存。中間WAVは `work/` に置き、Git管理から除外しています。
最終11個のMP3は全編デコード済みです。機械的な確認と、人による全編聴取は区別しています。
