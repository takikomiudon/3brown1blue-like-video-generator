#!/usr/bin/env python3
"""Shared VOICEVOX production path; resolve the saved user choice before synthesis."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener
import wave

DEFAULTS = Path(__file__).resolve().parents[1] / 'voice-defaults.json'
SETTINGS = dict(speedScale=1.04, pitchScale=-.015, intonationScale=1.0,
                volumeScale=1.0, prePhonemeLength=.12, postPhonemeLength=.14,
                outputSamplingRate=48000, outputStereo=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def choice():
    return json.loads(DEFAULTS.read_text())['speaker']


class Voicevox:
    def __init__(self, api='http://127.0.0.1:50021', settings=None):
        # Only the local engine bypasses the environment's Internet proxy.
        from urllib.parse import urlsplit
        if urlsplit(api).hostname not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('VOICEVOX API must use loopback')
        self.api = api.rstrip('/')
        self.opener = build_opener(ProxyHandler({}))
        requested = choice()
        speakers = self.get('/speakers')
        matches = [s for s in speakers if s['name'] == requested['name']
                   and s['speaker_uuid'] == requested['speaker_uuid']]
        styles = [s for speaker in matches for s in speaker['styles']
                  if s['name'] == requested['style']]
        if len(matches) != 1 or len(styles) != 1:
            raise RuntimeError('Selected VOICEVOX speaker/style is unavailable: '
                               + requested['name']+' / '+requested['style'])
        speaker, style = matches[0], styles[0]
        self.voice = dict(engine='VOICEVOX ENGINE', engine_version=self.get('/version'),
                          name=speaker['name'], speaker_uuid=speaker['speaker_uuid'],
                          style=style['id'], style_name=style['name'],
                          settings={**SETTINGS, **(settings or {})},
                          credit='VOICEVOX:'+speaker['name'], selection='voice-defaults.json')
        self.policy = self.get('/speaker_info?'+urlencode(
            {'speaker_uuid': speaker['speaker_uuid']}))['policy']

    def get(self, path):
        with self.opener.open(self.api+path, timeout=30) as response:
            return json.loads(response.read())

    def post(self, path, params, data=None):
        request = Request(self.api+path+'?'+urlencode(params),
                          data=json.dumps(data).encode() if data is not None else b'',
                          headers={'Content-Type': 'application/json'}, method='POST')
        with self.opener.open(request, timeout=300) as response:
            return response.read()

    def synthesize(self, text, wav):
        wav = Path(wav)
        wav.parent.mkdir(parents=True, exist_ok=True)
        queryfile, cachefile = wav.with_suffix('.query.json'), wav.with_suffix('.cache.json')
        key = hashlib.sha256(json.dumps([text, self.voice], sort_keys=True).encode()).hexdigest()
        cached = json.loads(cachefile.read_text()) if cachefile.exists() else {}
        reuse = (cached.get('key') == key and wav.exists() and queryfile.exists()
                 and cached.get('audio_sha256') == sha(wav)
                 and cached.get('query_sha256') == sha(queryfile))
        if not reuse:
            query = json.loads(self.post('/audio_query', {'text': text, 'speaker': self.voice['style']}))
            query.update(self.voice['settings'])
            write_json(queryfile, query)
            audio = self.post('/synthesis', {'speaker': self.voice['style']}, query)
            temporary = wav.with_suffix('.wav.tmp')
            temporary.write_bytes(audio)
            with wave.open(str(temporary)) as stream:
                if stream.getnframes() <= 0:
                    raise ValueError('Empty VOICEVOX output')
            temporary.replace(wav)
            cached = dict(key=key, audio_sha256=sha(wav), query_sha256=sha(queryfile))
            write_json(cachefile, cached)
        with wave.open(str(wav)) as stream:
            if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) != (48000, 1, 2):
                raise ValueError('Expected 48 kHz mono PCM16')
            duration = stream.getnframes()/stream.getframerate()
        return dict(text=text, audio=wav.name, query=queryfile.name,
                    speech_duration=duration, speaker_id=self.voice['style'],
                    speaker_uuid=self.voice['speaker_uuid'], **cached)

    def save_project(self, root, records, extra_audio=()):
        root = Path(root)
        (root/'assets').mkdir(exist_ok=True)
        (root/'assets/voice-policy.md').write_text(self.policy)
        write_json(root/'assets/voice.json', {**self.voice, 'records': records,
                   'defaults_sha256': sha(DEFAULTS),
                   'story_sha256': sha(root/'story.json'),
                   'timeline_sha256': sha(root/'timeline.json'),
                   'extra_audio': [{'audio': p, 'audio_sha256': sha(root/p)} for p in extra_audio]})


def verify_voice(voice):
    """Check the saved generation identity against the current user selection."""
    selected = choice()
    if (voice.get('name'), voice.get('speaker_uuid'), voice.get('style_name')) != (
            selected['name'], selected['speaker_uuid'], selected['style']):
        raise ValueError('Narrator differs from voice-defaults.json; run audio preparation again')
    if voice['credit'] != 'VOICEVOX:'+voice['name']:
        raise ValueError('Voice credit mismatch')
    if voice.get('defaults_sha256') != sha(DEFAULTS):
        raise ValueError('Voice defaults changed; prepare audio again')
    if not voice.get('records') or any(
            r.get('speaker_id') != voice['style'] or r.get('speaker_uuid') != voice['speaker_uuid']
            for r in voice['records']):
        raise ValueError('Missing or inconsistent synthesis speaker record')
    return voice


def verify_project(root):
    """Reject old/mismatched voice assets before a new render or finalization."""
    root = Path(root)
    voice = verify_voice(json.loads((root/'assets/voice.json').read_text()))
    for name in ('story', 'timeline'):
        if voice.get(name+'_sha256') != sha(root/(name+'.json')):
            raise ValueError(name+' changed; run audio preparation again')
    story = json.loads((root/'story.json').read_text())
    cues = json.loads((root/'timeline.json').read_text())
    records = voice.get('records', [])
    if not records or len(records) != len(story) or len(cues) != len(story):
        raise ValueError('Incomplete voice generation record')
    for line, cue, record in zip(story, cues, records):
        if line['say'] != record['text'] or cue['audio'] != 'audio/'+record['audio']:
            raise ValueError('Audio does not match story/timeline')
        for field, hashfield in [('audio', 'audio_sha256'), ('query', 'query_sha256')]:
            if sha(root/'audio'/record[field]) != record[hashfield]:
                raise ValueError('Generated '+field+' hash mismatch; prepare audio again')
    for extra in voice.get('extra_audio', []):
        if sha(root/extra['audio']) != extra['audio_sha256']:
            raise ValueError('Combined narration hash mismatch')
    return voice


def render_inputs(root):
    verify_project(root)
    return {name: sha(Path(root)/name) for name in
            ('assets/voice.json', 'story.json', 'timeline.json')}


def save_render(root, video, inputs):
    if inputs != render_inputs(root):
        raise ValueError('Audio inputs changed during render')
    write_json(Path(video).with_suffix('.voice.json'),
               {'inputs': inputs, 'video_sha256': sha(video)})


def verify_render(root, video):
    receipt_path = Path(video).with_suffix('.voice.json')
    if not receipt_path.exists():
        raise ValueError('Render has no narration receipt; prepare audio and render again')
    receipt = json.loads(receipt_path.read_text())
    if receipt != {'inputs': render_inputs(root), 'video_sha256': sha(video)}:
        raise ValueError('Render differs from current audio; render again')
    return verify_project(root)


def verify_delivery(root, video):
    """Bind the delivered file and its credit to the current narration manifest.

    Published files can be checked after a fresh clone, without ignored WAV caches.
    Decoding/listening remain separate checks; this verifies identity and hashes.
    """
    root, video = Path(root), Path(video)
    voice = verify_voice(json.loads((root/'assets/voice.json').read_text()))
    report = json.loads((video.parent/'validation.json').read_text())
    file_sha = report.get('sha256') or report.get('video_sha256')
    credit = report.get('voice') or report.get('voice_credit')
    if (file_sha != sha(video) or credit != voice['credit']
            or report.get('voice_manifest_sha256') != sha(root/'assets/voice.json')):
        raise ValueError('Delivery does not match current narration; regenerate and finalize again')
    audit_path = video.parent/'voice-track-audit.json'
    if not audit_path.exists() or report.get('voice_track_audit_sha256') != sha(audit_path):
        raise ValueError('Missing or changed embedded voice verification')
    audit = json.loads(audit_path.read_text())
    if (audit.get('status') != 'PASS' or audit.get('video_sha256') != file_sha
            or audit.get('voice_manifest_sha256') != report['voice_manifest_sha256']
            or audit.get('credit') != voice['credit']):
        raise ValueError('Embedded voice verification differs from this delivery')
    return voice


def prepare_story(root, subtitle=lambda cue: cue['say'], api='http://127.0.0.1:50021'):
    root = Path(root)
    engine = Voicevox(api=api)
    story = json.loads((root/'story.json').read_text())
    (root/'outputs').mkdir(exist_ok=True)
    timeline, records, cursor = [], [], 0
    for i, item in enumerate(story):
        wav = root/'audio'/f'{i:02}-{item["id"]}.wav'
        record = engine.synthesize(item['say'], wav)
        duration = math.ceil((record['speech_duration']+.85)*30)/30
        timeline.append({**item, 'index': i, 'audio': 'audio/'+wav.name, 'start': cursor,
                         'speech_duration': record['speech_duration'],
                         'duration': duration, 'end': cursor+duration})
        records.append(record)
        cursor += duration
        print(item['id'], round(record['speech_duration'], 2), engine.voice['credit'], flush=True)
    write_json(root/'timeline.json', timeline)
    def stamp(t):
        n = round(t*1000)
        return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
    (root/'outputs'/f'{root.name}-ja.srt').write_text('\n\n'.join(
        f'{i+1}\n{stamp(c["start"])} --> {stamp(c["start"]+c["speech_duration"])}\n{subtitle(c)}'
        for i, c in enumerate(timeline))+'\n')
    engine.save_project(root, records)
    return verify_project(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--api', default='http://127.0.0.1:50021')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--check-delivery', type=Path)
    args = parser.parse_args()
    if args.check_delivery:
        result = verify_delivery(args.project, args.check_delivery)
    else:
        result = verify_project(args.project) if args.check else prepare_story(args.project, api=args.api)
    print(result['credit'], '/ style', result['style'])
