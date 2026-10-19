"""Assemble the ten verified videos with scripts, sources, captions, and reproduction files."""
from pathlib import Path
import hashlib,json,zipfile,os,sys

ROOT=Path(__file__).resolve().parent
SKILL=Path(os.environ.get('SCIENCE_EXPLAINER_SKILL',
    ROOT/'science-explainer' if (ROOT/'science-explainer').exists() else ROOT.parent.parent/'.agents/skills/science-explainer'))
sys.path.insert(0,str(SKILL/'scripts'))
from voicevox_audio import verify_delivery

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    eps=json.loads((ROOT/'episodes.json').read_text());entries=[];credits=[]
    lines=['# RAGの現在地：10本のショート動画','',
      '2026年10月19日確認。日本語・1080×1920・24fps。音声と焼き込み字幕付き。',
      '基礎論文と2026年の研究・実装状況を区別して解説します。',
      '対象：RAGの基礎を知る初中級エンジニア。図は説明用の模式図です。','',
      '[10本・台本・字幕を一括ダウンロード](rag-trends-10-videos.zip)','',
      '|#|動画|時間|台本・一次資料|','|---|---|---|---|']
    for i,ep in enumerate(eps):
        d=ROOT/ep['slug'];v=d/'outputs/final.mp4'
        audit=json.loads((d/'outputs/motion-audit.json').read_text())
        valid=json.loads((d/'outputs/validation.json').read_text())
        verify_delivery(d, v)
        assert audit['status']=='PASS' and valid['full_decode']=='PASS'
        assert audit['video_sha256']==valid['video_sha256']==sha(v)
        credit=valid['voice_credit'];credits.append(credit)
        if 'voice_manifest_sha256' in valid:
            assert valid['voice_manifest_sha256']==sha(d/'assets/voice.json')
        duration=valid['duration_seconds']
        entries.append({'number':i+1,'title':ep['title'],'file':str(v.relative_to(ROOT)),
                        'duration_seconds':duration,'bytes':v.stat().st_size,'sha256':sha(v)})
        lines.append(f'|{i+1}|[{ep["title"]}]({ep["slug"]}/outputs/final.mp4)|{duration:.1f}秒|[台本と出典]({ep["slug"]}/script.md)|')
        description=ep['title']+'：'+ep['subtitle']+'\n\n'
        description+='\n'.join(f'{name}: {url}' for name,url in ep['sources'])
        description+='\n\n2026年10月19日時点で一次資料を確認。\n音声：'+credit+'\n'
        (d/'outputs/description.txt').write_text(description)
    lines+=['','各回は問い・仕組み・使いどころ・注意点・読む資料の5区間です。',
      '論文の主張や実験条件の詳細は、各回の台本から一次資料へ進んでください。','',
      '**音声：'+' / '.join(dict.fromkeys(credits))+'**。投稿時は付属のdescription.txtのクレジットを記載してください。','',
      '検証：全MP4の全編デコード、映像と音声の形式・尺、音量、字幕範囲、主図の動作検査、同じSHA-256に対応する連続フレームの意味レビューを実施。',
      '字幕は実測発話内の文字数配分による推定タイミングです。人による全編の音声聴取は未実施で、機械検査・クエリ確認と区別しています。','',
      '編集元はepisodes.jsonと各回のstory.json。合成クエリと音声設定を保存しています。',
      '[論文・ライブラリの読むリスト](reading-list.md) / [編集時の確認事項](research-notes.md) / [制作計画](plan.md) / [全出典](sources.json) / [納品ファイルのハッシュ](manifest.json)','',
      '## 再生成','',
      'DockerとホストのNoto Sans CJKフォントを使用。既存のdecay-heat-manim:0.20.1がない場合は同梱Dockerfileから作成します。',
      '初回の描画前に、pilot/review.jsonおよび各回のpilotレビューと対応する試作動画を参照してください。','',
      '```bash',
      'BUILDX_CONFIG=/tmp/rag-buildx docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t decay-heat-manim:0.20.1 .',
      'docker run -d --name rag-trends-voicevox -p 127.0.0.1:50021:50021 --cpus 3 voicevox/voicevox_engine@sha256:eb8c7f46a7d01217d1ff2b6f018261faedeceded3cc756b4fbbf371791ad6c90',
      '# /version が応答した後に実行',
      'python prepare.py --audio',
      'python run_batch.py --workers 2',
      'docker stop rag-trends-voicevox',
      '```','',
      '再生成後は新しい最終MP4をレビューし、そのSHA-256に対応するmotion-review.jsonでaudit_motion.pyを実行してください。過去のレビューを新しい動画に流用しないでください。']
    (ROOT/'README.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'manifest.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    include=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ['.md','.json','.py']]
    include+=[ROOT/'Dockerfile']
    include.extend(p for p in (ROOT/'pilot').glob('**/RagShort.mp4') if 'partial_movie_files' not in p.parts)
    include.extend((ROOT/'pilot').glob('**/review.json'))
    for ep in eps:
        d=ROOT/ep['slug']
        include.extend(d/name for name in ['script.md','story.json','sources.md','plan.md','timeline.json','motion-plan.json','motion-review.json'])
        include.extend(p for p in (d/'outputs').iterdir() if p.suffix in ['.mp4','.srt','.ass','.jpg','.json','.txt'])
        include.extend((d/'assets').glob('*'))
        include.extend((d/'audio').glob('*.query.json'))
    with zipfile.ZipFile(ROOT/'rag-trends-10-videos.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(include):z.write(p,str(p.relative_to(ROOT)))
        for name in ['voice-defaults.json','scripts/voicevox_audio.py','scripts/verify_voice_track.py']:
            z.write(SKILL/name,'science-explainer/'+name)
    archive=ROOT/'rag-trends-10-videos.zip'
    (ROOT/'archive.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
    print('PACKAGED',len(entries),'videos',round(archive.stat().st_size/1024/1024,1),'MiB')

if __name__=='__main__':main()
