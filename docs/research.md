# 科学解説動画の制作工程と調査結果

初回調査：2026-10-16。2026-10-18に会話履歴から復元。
対象は、Codexで継続編集・再生成できる日本語の図解動画。「3brown1blue」は3Blue1Brownの意図として扱った。
既存作品の映像・キャラクター・ナレーターの声は使わず、図形の変化によって仕組みを伝える。

## 工程ごとの既存ノウハウ

|工程|採用した方法|先行資料|出力・確認事項|
|---|---|---|---|
|1. アイデアと問い|対象視聴者と最後に理解できる因果関係を絞る。問いが視聴者の関心を引くかは別に検証する。|3b1b/manim、Manim Composer|対象・問い・理解の着地点|
|2. 科学資料|事実、仮定、概念図を分離し、実際に読めた出典を記録。教材にも一般化や不正確な箇所があるので転記しない。|OpenStax University Physics Vol.3|[科学的確認](fact-check.md)|
|3. 台本|一場面一論点。問い→観察→説明。読み上げ用の数値・英字を日本語にする。|Manim Composer、Remotionの場面管理|`story.json` を編集元にする|
|4. 絵コンテ|図、式、字幕、過去の結論の領域を決め、現在注目する対象を一つにする。|Remotion video-layout、Manim Video Lab|`plan.md`、キーフレーム|
|5. 音声と字幕|音声を先に作り、実測尺で動きと字幕を配置。作者と利用条件を確認。|pyopenjtalk-plus、VOICEVOX、Remotion captions|WAV、クエリ、タイムライン、SRT|
|6. アニメーション|図の変化が説明を担うようにし、対象の意味・色・位置の連続性を保つ。状態を決定論的に計算する。|Manim、Remotion timing、3b1b/videos|図、粒子、数値、曲線が同じ状態に従う|
|7. 編集と出力|試写を先に確認してから完成解像度へ。一般的なH.264/yuv420p/AAC、faststart。|Remotion render、FFmpeg|MP4、字幕、静止画|
|8. 検証と受け渡し|科学、画面、動き、音声、ファイル、保存先を別々に確認。再取得したファイルのハッシュを照合する。|Manim Video Lab、TEAの評価方法、本作の実際の失敗|検証JSON、GitHubの確定URL|

表の採用方針は資料を本作へ適用した判断。すべてが引用元で効果検証された法則という意味ではない。

## 技術選定の経緯

|候補|確認した特徴|本作での扱い|
|---|---|---|
|ManimGL / 3b1b/manim|説明アニメーション向け。OpenGL、Pango等の依存がある。|初回にREADMEを調査。実行には使っていない。|
|Manim Community|Python、数式、図形、変形、トラッカー。ManimGLとはAPIが別。|65秒ショートの実際の描画に採用。|
|Remotion|React、字幕、フレーム補間、エージェント向け公式スキル。|スキルを導入。動画の描画ランタイムには使っていない。|
|Pillow + FFmpeg|ブラウザ・GPUがなくても動く2D描画。|最初の4分動画に使用。|
|pyopenjtalk-plus / HTS Mei|APIキーなしの日本語音声。|最初の4分動画に使用。|
|VOICEVOX ENGINE|読み・話速・アクセントを扱える日本語音声API。|65秒ショートは青山龍星ノーマルを使用。|

最初の4分動画は一つのコマンドで再生成するPython方式。次のショートでは、導入した既存の演出手順を使ってManimへ移行した。

## 実際に取得した資料の記録

- [3b1b/manim](https://github.com/3b1b/manim)：初回README取得時のHEADは `fafa083a4fb274bba9cabde0b6e2f50ba6da0622`。
- [Remotion Agent Skills](https://github.com/remotion-dev/skills/tree/7ba4dcf8ebe1626b00baa41e1f2478113719b60b)：README、best-practices、create、video-layout、timing、sequencing、captionsを確認。
- [OpenStax公開教材](https://github.com/openstax/osbooks-university-physics-bundle/tree/2300d5b8ca2571dacc6ec25ebef56ba8d49000a2)：Vol.3の目次、m58609/10/11を確認。本文・図版の転載はしていない。
- [pyopenjtalk-plus](https://github.com/tsukumijima/pyopenjtalk-plus)：`0.4.1.post9` を導入しAPIと同梱音声のライセンスを確認。
- [米国DOE Nuclear 101](https://www.energy.gov/ne/articles/nuclear-101-how-does-nuclear-reactor-work)：HTTP 403で未取得。読んだ資料として扱わない。

追加の技術調査は[品質向上の調査](quality-upgrade.md)。復元したスキルの実ファイルの由来は [vendor-skills.json](vendor-skills.json)。
