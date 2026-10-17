# 原子炉を止めても、なぜ冷却が必要？

日本語音声・字幕付きの約65秒の縦型動画。

- [1080p動画をダウンロード](outputs/decay-heat-short-ja.mp4)
- [720p動画をダウンロード](outputs/decay-heat-short-ja-720p.mp4)
- [日本語字幕](outputs/decay-heat-ja.srt)

GitHub上で動画のプレビューが出ない場合は、ファイルページの **Download raw file** を選んでください。
完成動画と再生成コードをこのブランチに保存しています。

## 再生成

DockerとホストのNoto Sans CJKフォントを使用。Manim Community 0.20.1およびVOICEVOX ENGINE 0.25.2のイメージをダイジェストで固定。
`story.json` が台本、`prepare_audio.py` が音声とタイムライン、`script.py` がアニメーション、`finalize.py` が出力と検証。

```bash
BUILDX_CONFIG=/tmp/decay-heat-buildx docker build \
  --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt \
  -t decay-heat-manim:0.20.1 .
docker run -d --name decay-heat-voicevox -p 127.0.0.1:50021:50021 --cpus 2 \
  voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90
# /version が応答したら以下を実行
python3 prepare_audio.py
bash run.sh manim -qh -r 1080,1920 --fps 30 --disable_caching script.py DecayHeatShort
bash run.sh python finalize.py
docker stop decay-heat-voicevox
docker rm decay-heat-voicevox
```

音声が既にある場合は、音声生成を再実行する必要はありません。
核分裂生成物の放射性崩壊による発熱が停止後も残るため、冷却による熱の除去が必要という説明です。
図・粒子数・寸法・曲線・冷却系統は説明用の概念図で、実機の操作や定量的な温度・出力を示しません。
参考：OpenStax, University Physics Vol.3, Radioactive Decay / Nuclear Reactions / Fission。
図と原稿は本プロジェクトで新規制作。

**音声：VOICEVOX:青山龍星**。エンジンから取得した利用条件は `assets/voice-policy.md`。
公開時は投稿文にも音声クレジットを記載してください。

制作の設計は、Manim Video Labの対象の連続性、注目対象、語の時刻に合わせた表示、実際のレンダーの確認という既存の手法を参考にしています。
