#!/usr/bin/env python3
"""Synthesize a speaker comparison with equal source parameters and output loudness."""
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import build_opener, ProxyHandler, Request
import array
import hashlib
import json
import math
import re
import subprocess
import wave
import zipfile

ROOT = Path(__file__).resolve().parent
API = 'http://127.0.0.1:50021'
OPENER = build_opener(ProxyHandler({}))  # Loopback API only.
WORK, OUT, ASSETS = ROOT/'work', ROOT/'outputs', ROOT/'assets'


def get(path):
    return json.loads(OPENER.open(API+path, timeout=30).read())


def post(path, data=None, params=None):
    url = API+path+('?' + urlencode(params) if params else '')
    request = Request(url, data=json.dumps(data).encode() if data is not None else b'',
                      headers={'Content-Type': 'application/json'}, method='POST')
    return OPENER.open(request, timeout=180).read()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def synth(text, style, settings, engine, stem):
    path = WORK/(stem+'.wav')
    cache = WORK/(stem+'.sha256')
    key = hashlib.sha256(json.dumps([text, style, settings, engine], sort_keys=True).encode()).hexdigest()
    if not path.exists() or not cache.exists() or cache.read_text() != key:
        query = json.loads(post('/audio_query', params={'text': text, 'speaker': style}))
        query.update(settings)
        (ASSETS/(stem+'.query.json')).write_text(json.dumps(query, ensure_ascii=False, indent=2)+'\n')
        path.write_bytes(post('/synthesis', data=query, params={'speaker': style}))
        cache.write_text(key)
    with wave.open(str(path)) as stream:
        assert (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) == (48000, 1, 2)
        pcm = array.array('h', stream.readframes(stream.getnframes()))
        assert pcm and 0 < max(map(abs, pcm)) < 32767
    return path


def normalize(source, stem):
    result = run(['ffmpeg', '-hide_banner', '-i', str(source), '-vn', '-af',
                  'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                 capture_output=True, text=True)
    levels = json.loads(re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)[-1])
    assert math.isfinite(float(levels['input_i']))
    af = 'loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:' + ':'.join(
        f'{dest}={levels[src]}' for dest, src in [('measured_I', 'input_i'),
        ('measured_TP', 'input_tp'), ('measured_LRA', 'input_lra'),
        ('measured_thresh', 'input_thresh'), ('offset', 'target_offset')])
    normalized = WORK/(stem+'-normalized.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-af', af,
         '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(normalized)])
    (ASSETS/(stem+'.loudness.json')).write_text(json.dumps(levels, indent=2)+'\n')
    return normalized


def encode(source, target, title, artist, track=None):
    args = ['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-c:a', 'libmp3lame',
            '-q:a', '2', '-ar', '48000', '-ac', '1', '-metadata', 'title='+title,
            '-metadata', 'artist='+artist, '-metadata', 'album=VOICEVOX 10話者 比較']
    if track:
        args += ['-metadata', 'track='+track]
    run(args+[str(target)])


def validate(path):
    meta = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                                               '-show_streams', '-of', 'json', str(path)]))
    assert len(meta['streams']) == 1
    stream = meta['streams'][0]
    assert (stream['codec_type'], stream['codec_name'], stream['channels']) == ('audio', 'mp3', 1)
    assert int(stream['sample_rate']) == 48000
    duration = float(meta['format']['duration'])
    assert duration > 1
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'])
    levels = run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'volumedetect',
                  '-f', 'null', '-'], capture_output=True, text=True)
    peak = float(re.search(r'max_volume: ([-\d.]+) dB', levels.stderr)[1])
    assert peak < -.1
    return {'file': path.name, 'duration_seconds': duration, 'size_bytes': path.stat().st_size,
            'sha256': sha(path), 'peak_dbfs': peak, 'full_decode': 'passed',
            'format': 'MP3 / 48kHz / mono'}


def main():
    for directory in [WORK, OUT, ASSETS]:
        directory.mkdir(exist_ok=True)
    config = json.loads((ROOT/'config.json').read_text())
    engine, roster = get('/version'), get('/speakers')
    records, normalized, total_frames = [], [], 0
    combined_wav = WORK/'comparison.wav'
    with wave.open(str(combined_wav), 'wb') as combined:
        combined.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        for index, item in enumerate(config['speakers'], 1):
            speaker = next(s for s in roster if s['name'] == item['name'])
            style = next(s for s in speaker['styles'] if s['name'] == item['style'])
            stem = f'{index:02}-{item["slug"]}'
            info = get('/speaker_info?'+urlencode({'speaker_uuid': speaker['speaker_uuid']}))
            (ASSETS/(stem+'.policy.md')).write_text(info['policy'])
            raw = synth(config['synthesis_text'], style['id'], config['settings'], engine, stem)
            intro = synth(f'{index}番、{item["reading"]}です。', style['id'],
                          config['settings'], engine, stem+'-intro')
            sample_normalized = normalize(raw, stem)
            intro_normalized = normalize(intro, stem+'-intro')
            target = OUT/(stem+'.mp3')
            credit = 'VOICEVOX:'+item['name']
            encode(sample_normalized, target, item['name']+'（'+item['style']+'）', credit, f'{index}/10')
            start = total_frames/48000
            for part in [intro_normalized, .45, sample_normalized, .9]:
                if isinstance(part, float):
                    frames = round(48000*part)
                    combined.writeframes(b'\0\0'*frames)
                else:
                    with wave.open(str(part)) as audio:
                        frames = audio.getnframes()
                        combined.writeframes(audio.readframes(frames))
                total_frames += frames
            record = {**item, 'index': index, 'style_id': style['id'], 'speaker_uuid': speaker['speaker_uuid'],
                      'credit': credit, 'raw_sha256': sha(raw),
                      'comparison_start_seconds': start, **validate(target)}
            records.append(record)
            print(index, item['name'], round(record['duration_seconds'], 2), 'seconds: passed', flush=True)
    comparison = OUT/'voicevox-10-comparison.mp3'
    encode(combined_wav, comparison, 'VOICEVOX 10話者 聴き比べ', ' / '.join(r['credit'] for r in records))
    aggregate = validate(comparison)
    assert abs(aggregate['duration_seconds']-total_frames/48000) < .1
    (OUT/'validation.json').write_text(json.dumps({'engine': 'VOICEVOX ENGINE',
        'engine_version': engine, 'settings': config['settings'], 'sample_count': len(records),
        'sample_text': config['text'], 'selection': config['selection'],
        'loudness_target': {'I_LUFS': -16, 'TP_dBTP': -1.5, 'LRA': 11},
        'samples': records, 'comparison': aggregate}, ensure_ascii=False, indent=2)+'\n')
    (OUT/'playlist.m3u').write_text('#EXTM3U\n'+'\n'.join(
        f'#EXTINF:{r["duration_seconds"]:.2f},{r["index"]:02} {r["name"]}\n{r["file"]}' for r in records)+'\n')
    def clock(seconds):
        n=int(seconds)
        return f'{n//60:02}:{n%60:02}'
    lines = ['VOICEVOX 10話者 比較', '番号は比較用で、人気順位ではありません。',
             '共通原稿：'+config['text'], '全員ノーマル、話速1.0、ピッチ0。出力音量は同じ基準へ調整。',
             '比較版は各話者の番号と名前を読み上げてから共通原稿を再生します。', '']
    for r in records:
        lines.append(f'{r["index"]:02} / {clock(r["comparison_start_seconds"])} / {r["name"]} / {r["credit"]}')
    (OUT/'voice-list.txt').write_text('\n'.join(lines)+'\n')
    bundle = OUT/'voicevox-10-audio.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.glob('*.mp3')):
            archive.write(path, path.name)
        for name in ['voice-list.txt', 'playlist.m3u']:
            archive.write(OUT/name, name)
    print('Comparison:', aggregate['duration_seconds'], 'seconds; ZIP:', bundle.stat().st_size, flush=True)


if __name__ == '__main__':
    main()
