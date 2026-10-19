"""Mux captions and VOICEVOX audio, verify streams, decode, inspect motion, make review sheets."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
import os, sys
SKILL = Path(os.environ.get('SCIENCE_EXPLAINER_SKILL',
    (ROOT/'science-explainer' if (ROOT/'science-explainer').exists() else ROOT.parent.parent / '.agents/skills/science-explainer')))
sys.path.insert(0, str(SKILL / 'scripts'))
from voicevox_audio import verify_render, verify_delivery
from verify_voice_track import save_audit
AUDIT=SKILL/'scripts/audit_motion.py'
SPELLINGS={
 'グラフラグ':'GraphRAG','ライトラグ':'LightRAG','ケーエージー':'KAG','ラプター':'RAPTOR',
 'セルフラグ':'Self-RAG','コレクティブ・ラグ':'Corrective RAG','シーラグ':'CRAG',
 'エージェンティック・アール':'Agentic-R','エムティーラグ・ユーエヌ':'MTRAG-UN',
 'ビージーイー・エムスリー':'BGE-M3','エムスリー・エンベディング':'M3-Embedding',
 'フラッグエンベディング':'FlagEmbedding','コルパリ':'ColPali','ドクリング':'Docling',
 'ランググラフ':'LangGraph','ラマインデックス':'LlamaIndex','ヘイスタック':'Haystack',
 'ラガス':'Ragas','ラグエニシング':'RAG-Anything','オープンエスピージー':'OpenSPG',
 'フロム・ローカル・トゥー・グローバル':'From Local to Global',
 'エイチケーユーディーエス':'HKUDS','エルエルエム':'LLM','ピーディーエフ':'PDF',
 'ラグ':'RAG'}

def run(args,**kw):return subprocess.run(args,check=True,**kw)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def ass_time(t):
    c=round(t*100);return f'{c//360000}:{c//6000%60:02}:{c//100%60:02}.{c%100:02}'
def seconds(ts):
    a,b,c=ts.replace(',','.').split(':');return int(a)*3600+int(b)*60+float(c)
def wrap(text):
    # Font-aware wrapping keeps English technical terms readable inside the safe zone.
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',44,index=0)
    lines=[];current=''
    for ch in text:
        if font.getlength(current+ch)>818 and current:
            lines.append(current);current=''
        current+=ch
    if current:lines.append(current)
    if len(lines)>3:raise ValueError('Subtitle is too long: '+text)
    return r'\N'.join(lines)

def check_audio(folder):
    result=subprocess.run(['ffmpeg','-hide_banner','-i',str(folder/'outputs/final.mp4'),'-vn',
       '-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],
       capture_output=True,text=True,check=True)
    measurement=json.loads(re.findall(r'\{[^{}]+\}',result.stderr)[-1])
    assert -17 <= float(measurement['input_i']) <= -15,measurement
    assert float(measurement['input_tp']) <= -1.0,measurement
    (folder/'outputs/final-audio-measurement.json').write_text(json.dumps(measurement,indent=2)+'\n')
    return {'integrated_lufs':float(measurement['input_i']),
            'true_peak_dbtp':float(measurement['input_tp'])}

def make_ass(folder):
    content=(folder/'outputs/captions.srt').read_text()
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK JP,44,&H00F2F6FF,&H00F2F6FF,&H0008111F,&H9008111F,0,0,0,0,100,100,0,0,1,3,0,8,100,160,1515,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events=[];last=0
    for block in content.strip().split('\n\n'):
        _,timing,spoken=block.split('\n',2)
        start,end=map(seconds,timing.split(' --> '))
        assert start>=last-.002 and end>start
        last=end
        display=spoken
        for a,b in SPELLINGS.items():display=display.replace(a,b)
        display=display.replace('\n','')
        events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{wrap(display)}')
    (folder/'outputs/captions.ass').write_text(header+'\n'.join(events)+'\n')
    return len(events),last

def finish(slug):
    folder=ROOT/slug;output=folder/'outputs/final.mp4'
    raw=ROOT/'work'/slug/'videos/render/1920p24/RagShort.mp4'
    voice = verify_render(folder, raw)
    cues=json.loads((folder/'timeline.json').read_text());duration=cues[-1]['end']+2
    count,last=make_ass(folder)
    assert last<cues[-1]['end']
    # Two-pass loudness, preserving all speech and the end-card silence.
    analysis=subprocess.run(['ffmpeg','-hide_banner','-i',str(folder/'audio/narration.wav'),'-af',
       'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    measured=json.loads(re.findall(r'\{[^{}]+\}',analysis.stderr)[-1])
    (folder/'outputs/loudness-measurement.json').write_text(json.dumps(measured,indent=2)+'\n')
    loud=(f'loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={measured["input_i"]}:'
          f'measured_TP={measured["input_tp"]}:measured_LRA={measured["input_lra"]}:'
          f'measured_thresh={measured["input_thresh"]}:offset={measured["target_offset"]}:linear=true')
    run(['ffmpeg','-v','error','-y','-threads','2','-i',str(raw),'-i',str(folder/'audio/narration.wav'),
         '-vf',f'ass={folder}/outputs/captions.ass','-af',loud,'-c:v','libx264','-threads','2',
         '-preset','fast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000',
         '-t',str(duration),'-movflags','+faststart','-metadata','comment=音声：'+voice['credit'],str(output)])
    info=probe(output);v=next(s for s in info['streams'] if s['codec_type']=='video')
    a=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1080,1920) and v['pix_fmt']=='yuv420p'
    assert v['avg_frame_rate']=='24/1' and a['codec_name']=='aac'
    assert abs(float(info['format']['duration'])-duration)<.15
    assert abs(float(a['duration'])-duration)<.15
    run(['ffmpeg','-v','error','-threads','1','-i',str(output),'-f','null','-'])
    audio_measurement=check_audio(folder)
    validation={'video_sha256':sha(output),'duration_seconds':float(info['format']['duration']),
      'width':v['width'],'height':v['height'],'fps':v['avg_frame_rate'],'audio_codec':a['codec_name'],
      'audio_duration_seconds':float(a['duration']),'full_decode':'PASS','subtitles':count,
      'subtitle_timing':'character-weighted estimate within measured utterances',
      'voice_credit':voice['credit'],'voice_manifest_sha256':sha(folder/'assets/voice.json'),'auditory_full_listen':'not_performed',
      'notes':'音声の聴取評価と機械検査は区別。図は模式図で実測性能値を示していない。',
      **audio_measurement}
    validation['voice_track_audit_sha256'] = save_audit(folder, output)
    (folder/'outputs/validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    run(['ffmpeg','-v','error','-y','-ss','3','-i',str(output),'-frames:v','1',str(folder/'outputs/poster.jpg')])
    verify_delivery(folder, output)
    print(slug,'FINISHED',round(duration,2),flush=True)
    return validation

def sheets(slug):
    folder=ROOT/slug;review=folder/'review-frames';review.mkdir(exist_ok=True)
    video=folder/'outputs/final.mp4';cues=json.loads((folder/'timeline.json').read_text())
    # Three states per beat, spanning the first three/four meaningful operations.
    samples=[];sheet=Image.new('RGB',(1050,1200),'#08111f');draw=ImageDraw.Draw(sheet)
    for row,cue in enumerate(cues):
        ts=[cue['start']+cue['duration']*fraction for fraction in [.13,.46,.84]]
        samples.append({'beat_id':cue['id'],'times':ts})
        for col,t in enumerate(ts):
            path=review/f'{row}-{col}.png'
            run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',
                 '-vf','crop=960:930:45:490,scale=350:-1',str(path)])
            im=Image.open(path).convert('RGB');im.thumbnail((350,215))
            sheet.paste(im,(col*350,row*240+23));draw.text((col*350+8,row*240+4),f'beat {row} | {t:.2f}s',fill='white')
    sheet.save(review/'mechanisms.jpg')
    # Full frames verify titles, captions, credit, and safety margins for each beat.
    full=Image.new('RGB',(1350,480),'#08111f')
    for i,cue in enumerate(cues):
        path=review/f'full-{i}.png'
        run(['ffmpeg','-v','error','-y','-ss',str(cue['start']+cue['duration']*.52),'-i',str(video),
             '-frames:v','1','-vf','scale=270:480',str(path)])
        full.paste(Image.open(path),(i*270,0))
    full.save(review/'layout.jpg')
    (review/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--sheets',action='store_true');a=ap.parse_args()
    if a.sheets:sheets(a.slug)
    else:finish(a.slug)
