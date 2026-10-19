"""Persist per-episode editorial material and synthesize measured VOICEVOX audio."""
from pathlib import Path
import argparse, hashlib, json, math, re, wave
from urllib.request import build_opener, ProxyHandler, Request
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent
API = 'http://127.0.0.1:50021'
OPENER = build_opener(ProxyHandler({}))
SETTINGS = dict(speedScale=1.10, pitchScale=-.015, intonationScale=1.0,
                volumeScale=1.0, prePhonemeLength=.12, postPhonemeLength=.18,
                outputSamplingRate=48000, outputStereo=False)

def get(path):
    return json.loads(OPENER.open(API+path, timeout=120).read())

def post(path, params, data=None):
    req = Request(API+path+'?'+urlencode(params),
                  data=json.dumps(data).encode() if data is not None else b'',
                  headers={'Content-Type':'application/json'}, method='POST')
    return OPENER.open(req, timeout=300).read()

def stamp(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audio',action='store_true')
    args=ap.parse_args()
    episodes=json.loads((ROOT/'episodes.json').read_text())
    if args.audio:
        engine=get('/version');speakers=get('/speakers')
        speaker=next(s for s in speakers if s['name']=='青山龍星')
        style=next(s for s in speaker['styles'] if s['name']=='ノーマル')
        policy=get('/speaker_info?'+urlencode({'speaker_uuid':speaker['speaker_uuid']}))['policy']
    overview=['# RAGの現在地：10本のショート動画', '',
      '確認日：2026年10月19日。日本語の初中級エンジニア向け。',
      '2023–2024年の基礎論文と2026年の研究・実装状況を区別する。',
      '性能の順位付けや網羅的な最新論文ランキングではない。', '',
      '音声：VOICEVOX:青山龍星。図は本シリーズで制作した模式図。', '']
    for ep in episodes:
        folder=ROOT/ep['slug']
        for name in ['assets','audio','outputs']:(folder/name).mkdir(parents=True,exist_ok=True)
        story=[{'id':f'beat-{i}','heading':s[0],'caption':s[1],'say':s[2]}
               for i,s in enumerate(ep['scenes'])]
        (folder/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n')
        source_text='\n'.join(f'- [{name}]({url})' for name,url in ep['sources'])
        (folder/'sources.md').write_text(f'# {ep["title"]}：出典\n\n確認日：2026年10月19日\n\n{source_text}\n')
        editorial=f'# {ep["title"]}\n\n{ep["subtitle"]}\n\n{ep["tag"]}\n\n'
        for i,item in enumerate(story):
            editorial+=f'## {i+1}. {item["heading"]}\n\n画面：{item["caption"]}\n\nナレーション：{item["say"]}\n\n'
        editorial+='## 出典\n\n'+source_text+'\n\n音声：VOICEVOX:青山龍星\n'
        (folder/'script.md').write_text(editorial)
        overview+= [f'## {ep["title"]}', '', ep['subtitle'], '',
                    f'- [動画]({ep["slug"]}/outputs/final.mp4)',
                    f'- [台本・出典]({ep["slug"]}/script.md)', '']
        if not args.audio:continue
        voice={'engine':'VOICEVOX ENGINE','engine_version':engine,'speaker':speaker['name'],
               'speaker_uuid':speaker['speaker_uuid'],'style':style,'settings':SETTINGS,
               'credit':'VOICEVOX:青山龍星'}
        (folder/'assets/voice.json').write_text(json.dumps(voice,ensure_ascii=False,indent=2)+'\n')
        (folder/'assets/voice-policy.md').write_text(policy)
        timeline=[];cursor=0;subtitles=[];parts=[]
        for i,item in enumerate(story):
            wav=folder/'audio'/f'{i:02}.wav'
            key=hashlib.sha256(json.dumps([item['say'],voice],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            keyfile=wav.with_suffix('.sha256')
            if not wav.exists() or not keyfile.exists() or keyfile.read_text()!=key:
                query=json.loads(post('/audio_query',{'text':item['say'],'speaker':style['id']}))
                query.update(SETTINGS)
                wav.with_suffix('.query.json').write_text(json.dumps(query,ensure_ascii=False,indent=2)+'\n')
                wav.write_bytes(post('/synthesis',{'speaker':style['id']},query));keyfile.write_text(key)
            with wave.open(str(wav)) as f:
                assert f.getframerate()==48000 and f.getnchannels()==1 and f.getsampwidth()==2
                frames=f.readframes(f.getnframes());seconds=len(frames)/96000
            duration=math.ceil((seconds+.45)*24)/24
            timeline.append({**item,'start':cursor,'end':cursor+duration,'duration':duration,
                             'speech_duration':seconds,'audio':f'audio/{i:02}.wav',
                             'audio_sha256':hashlib.sha256(wav.read_bytes()).hexdigest()})
            parts.append(frames+b'\0'*round((duration-seconds)*96000))
            # Caption timing is an approximate character-weighted segmentation per measured utterance.
            chunks=[]
            for sentence in re.findall(r'[^。！？]+[。！？]?',item['say']):
                while len(sentence)>40:
                    cut=sentence.rfind('、',10,39)+1
                    if cut<11:cut=34
                    chunks.append(sentence[:cut]);sentence=sentence[cut:]
                if sentence:chunks.append(sentence)
            offset=.12;usable=max(seconds-.30,0);total=sum(map(len,chunks))
            for chunk in chunks:
                span=usable*len(chunk)/total
                subtitles.append((cursor+offset,cursor+offset+span,chunk));offset+=span
            cursor+=duration
            print(ep['slug'],i,round(seconds,2),flush=True)
        with wave.open(str(folder/'audio/narration.wav'),'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(48000)
            out.writeframes(b''.join(parts)+b'\0'*192000)
        (folder/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
        (folder/'outputs/captions.srt').write_text('\n\n'.join(
            f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for i,(a,b,s) in enumerate(subtitles))+'\n')
        print('TOTAL',ep['slug'],cursor+2,flush=True)
    (ROOT/'README.md').write_text('\n'.join(overview)+'\n')

if __name__=='__main__':main()
