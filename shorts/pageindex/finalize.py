from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
SOURCE=ROOT/'media/videos/script/1920p30/PageIndexShort.mp4'
FINAL=OUT/'pageindex-short-ja.mp4'

def main():
    cues=json.loads((ROOT/'timeline.json').read_text())
    story=json.loads((ROOT/'story.json').read_text())
    assert len(cues)==len(story)==9
    for i,(cue,line) in enumerate(zip(cues,story)):
        assert cue['id']==line['id'] and cue['say']==line['say']
        assert cue['start']+(cue['speech_duration'])<cue['end']
        assert abs(cue['start']-(cues[i-1]['end'] if i else 0))<.0001
        assert (ROOT/cue['audio']).is_file()
    expected=cues[-1]['end']+2.5
    measure=subprocess.run(['ffmpeg','-hide_banner','-i',str(SOURCE),'-vn',
        '-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    values=json.loads(re.findall(r'\{\s*"input_i".*?\}',measure.stderr,re.S)[-1])
    (OUT/'loudness-measurement.json').write_text(json.dumps(values,indent=2)+'\n')
    af='loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:'+':'.join(
        f'{dst}={values[src]}' for dst,src in [('measured_I','input_i'),('measured_TP','input_tp'),
        ('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    af+=f',apad=whole_dur={expected:.9f}'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(SOURCE),'-map','0:v:0','-map','0:a:0',
        '-c:v','copy','-frames:v',str(round(expected*30)),'-af',af,'-c:a','aac','-b:a','192k',
        '-t',f'{expected:.9f}','-movflags','+faststart',str(FINAL)],check=True)
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(FINAL)]))
    v=next(s for s in meta['streams'] if s['codec_type']=='video')
    a=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['codec_name'],v['pix_fmt'])==(1080,1920,'h264','yuv420p')
    assert v['r_frame_rate']=='30/1' and a['codec_name']=='aac'
    assert abs(float(a['duration'])-expected)<.15
    assert abs(float(meta['format']['duration'])-expected)<.12
    assert int(v['nb_frames'])==round(expected*30)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(FINAL),'-f','null','-'],check=True)
    levels=subprocess.run(['ffmpeg','-hide_banner','-i',str(FINAL),'-vn','-af','volumedetect','-f','null','-'],
        capture_output=True,text=True,check=True)
    peak=float(re.search(r'max_volume: ([-\d.]+) dB',levels.stderr)[1]);assert peak<-.1
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(expected-3.5),'-i',str(FINAL),'-frames:v','1','-q:v','2',str(OUT/'poster.jpg')],check=True)
    # Secondary MP4 for older devices. The original-quality video is preserved.
    fallback=OUT/'pageindex-short-ja-720p.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(FINAL),'-vf','scale=720:1280',
        '-c:v','libx264','-profile:v','main','-level:v','3.1','-preset','fast','-crf','21','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','128k','-movflags','+faststart',str(fallback)],check=True)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(fallback),'-f','null','-'],check=True)
    fallback_meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(fallback)]))
    fv=next(s for s in fallback_meta['streams'] if s['codec_type']=='video')
    assert (fv['width'],fv['height'],fv['codec_name'],fv['pix_fmt'])==(720,1280,'h264','yuv420p')
    assert fv['profile']=='Main' and fv['level']==31
    report={'file':FINAL.name,'duration_seconds':float(meta['format']['duration']),
        'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'frames':int(v['nb_frames']),
        'audio_max_dbfs':peak,'full_decode':'passed','size_bytes':FINAL.stat().st_size,
        'sha256':hashlib.sha256(FINAL.read_bytes()).hexdigest(),'voice':'VOICEVOX:青山龍星',
        'cue_count':len(cues),'speech_within_cues':'passed',
        'story_sha256':hashlib.sha256((ROOT/'story.json').read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256((ROOT/'script.py').read_bytes()).hexdigest(),
        'source_commit':'e7d1cc67e4dd5bfe4cac63b161b313ef41328705',
        'fallback':{'file':fallback.name,'size_bytes':fallback.stat().st_size,
            'sha256':hashlib.sha256(fallback.read_bytes()).hexdigest(),'full_decode':'passed',
            'width':fv['width'],'height':fv['height'],'profile':fv['profile'],'level':fv['level']}}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
