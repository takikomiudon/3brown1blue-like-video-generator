#!/usr/bin/env python3
"""Match each decoded MP4 utterance to its verified VOICEVOX source WAV.

AAC encoding and loudness normalization change bytes, so compare normalized PCM
correlation with a small alignment allowance. This is not a listening review.
Uses Python's standard library and ffmpeg; source WAVs must be present.
"""
import argparse
from array import array
import json
import math
from pathlib import Path
import subprocess
import sys

from voicevox_audio import sha, verify_project, write_json

RATE = 8000
MIN_CORRELATION = .85


def pcm(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                                   '-vn', '-ac', '1', '-ar', str(RATE), '-f', 'f32le', '-'])
    samples = array('f', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    return samples


def correlate(reference, rendered, start):
    # Use up to 2000 interior samples and search +/- 120 ms at 1 ms resolution.
    margin = round(.2*RATE)
    usable = len(reference)-2*margin
    if usable <= 0:
        raise ValueError('Utterance is too short for PCM matching')
    stride = max(8, usable//2000)
    indices = list(range(margin, len(reference)-margin, stride))
    values = [reference[i] for i in indices]
    energy = sum(v*v for v in values)
    if energy <= 1e-10:
        raise ValueError('No speech energy in reference WAV')

    def score(lag):
        offsets = [start+i+lag for i in indices]
        if offsets[0] < 0 or offsets[-1] >= len(rendered):
            return -1
        other = [rendered[i] for i in offsets]
        other_energy = sum(v*v for v in other)
        if other_energy <= 1e-10:
            return 0
        return sum(a*b for a, b in zip(values, other))/math.sqrt(energy*other_energy)

    coarse = max(range(-960, 961, 8), key=score)
    fine = max(range(coarse-7, coarse+8), key=score)
    return score(fine), fine/RATE


def verify(root, video):
    root, video = Path(root), Path(video)
    voice = verify_project(root)
    rendered = pcm(video)
    cues = json.loads((root/'timeline.json').read_text())
    checks = []
    for cue in cues:
        reference = pcm(root/cue['audio'])
        correlation, offset = correlate(reference, rendered, round(cue['start']*RATE))
        checks.append({'id': cue['id'], 'reference_sha256': sha(root/cue['audio']),
                       'correlation': round(correlation, 6), 'offset_seconds': offset,
                       'status': 'PASS' if correlation >= MIN_CORRELATION else 'FAIL'})
    return {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
            'video_sha256': sha(video), 'voice_manifest_sha256': sha(root/'assets/voice.json'),
            'credit': voice['credit'], 'speaker_id': voice['style'],
            'method': 'Normalized PCM correlation against each source utterance',
            'minimum_correlation': MIN_CORRELATION, 'checks': checks,
            'human_listening': 'not_performed'}


def save_audit(root, video):
    result = verify(root, video)
    path = Path(video).parent/'voice-track-audit.json'
    write_json(path, result)
    if result['status'] != 'PASS':
        raise ValueError('Embedded speech does not match the selected VOICEVOX source WAVs')
    return sha(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('video', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.project, args.video)
    write_json(args.output, result)
    print(result['status'], result['credit'], [c['correlation'] for c in result['checks']])
    sys.exit(0 if result['status'] == 'PASS' else 1)
