from pathlib import Path
from urllib.request import build_opener, ProxyHandler, Request
from urllib.parse import urlencode
import hashlib, json, math, wave
ROOT=Path(__file__).resolve().parent
API='http://127.0.0.1:50021'
STYLE=13
opener=build_opener(ProxyHandler({}))

def call(path,data=None,params=None):
    url=API+path+('?' + urlencode(params) if params else '')
    req=Request(url,data=json.dumps(data).encode() if data is not None else b'',
                headers={'Content-Type':'application/json'},method='POST')
    return opener.open(req,timeout=180).read()

def main():
    story=json.loads((ROOT/'story.json').read_text()); timeline=[]; cursor=0
    (ROOT/'audio').mkdir(exist_ok=True);(ROOT/'outputs').mkdir(exist_ok=True)
    for i,item in enumerate(story):
        file=ROOT/'audio'/f'{i:02}-{item["id"]}.wav'
        key=hashlib.sha256((item['say']+'|13|1.04|48000').encode()).hexdigest()
        keyfile=file.with_suffix('.sha256')
        if not file.exists() or not keyfile.exists() or keyfile.read_text()!=key:
            query=json.loads(call('/audio_query',params={'text':item['say'],'speaker':STYLE}))
            query.update(speedScale=1.04,volumeScale=1.0,pitchScale=-.015,
                         prePhonemeLength=.12,postPhonemeLength=.14,outputSamplingRate=48000)
            file.with_suffix('.query.json').write_text(json.dumps(query,ensure_ascii=False,indent=2))
            file.write_bytes(call('/synthesis',data=query,params={'speaker':STYLE}));keyfile.write_text(key)
        with wave.open(str(file)) as f: seconds=f.getnframes()/f.getframerate()
        duration=math.ceil((seconds+.85)*30)/30
        timeline.append({**item,'index':i,'audio':str(file.relative_to(ROOT)),
            'start':cursor,'speech_duration':seconds,'duration':duration,'end':cursor+duration})
        cursor+=duration;print(item['id'],round(seconds,2),flush=True)
    (ROOT/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n')
    def ts(t):
        n=round(t*1000);return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
    (ROOT/'outputs/decay-heat-ja.srt').write_text('\n\n'.join(
        f'{i+1}\n{ts(c["start"])} --> {ts(c["start"]+c["speech_duration"])}\n{c["say"]}'
        for i,c in enumerate(timeline))+'\n')
    speakers=json.loads(opener.open(API+'/speakers').read())
    speaker=next(s for s in speakers if any(t['id']==STYLE for t in s['styles']))
    info=json.loads(opener.open(API+'/speaker_info?'+urlencode({'speaker_uuid':speaker['speaker_uuid']})).read())
    (ROOT/'assets/voice-policy.md').write_text(info['policy'])
    (ROOT/'assets/voice.json').write_text(json.dumps({'name':speaker['name'],'style':STYLE,
        'credit':'VOICEVOX:青山龍星','engine_version':json.loads(opener.open(API+'/version').read())},ensure_ascii=False,indent=2)+'\n')
    print('Total:',cursor+2.5,flush=True)
if __name__=='__main__':main()
