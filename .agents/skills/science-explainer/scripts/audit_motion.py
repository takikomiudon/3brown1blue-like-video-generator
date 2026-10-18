#!/usr/bin/env python3
"""Measure subject-region temporal changes and bind semantic review to the MP4.

Exit 0: measurements and supplied semantic review pass; 1: failed; 2: review needed.
--mechanical-only is for diagnostics, not production acceptance.
Dependencies: Python stdlib, ffmpeg, ffprobe.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

FPS = 10
CHANGE_THRESHOLD = 16
MIN_CHANGED_AREA = .0005
MIN_ACTIVE_SHARE = .12
MIN_CONTINUOUS_CHANGE_SECONDS = .3
MAX_UNEXPLAINED_HOLD_SECONDS = 4.0


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def overlap(a, b, c, d):
    return max(0.0, min(b, d) - max(a, c))


def validate_plan(plan, duration):
    roi = plan['roi']
    if (not isinstance(roi, list) or len(roi) != 4 or not all(number(n) for n in roi)
            or min(roi) < 0 or min(roi[2:]) <= 0
            or roi[0] + roi[2] > 1.000001 or roi[1] + roi[3] > 1.000001):
        raise ValueError('roi must be normalized [x, y, width, height] within the frame')
    beats = plan['beats']
    if not isinstance(beats, list) or not beats:
        raise ValueError('A complete beat sequence is required')
    cursor, ids = 0, set()
    for beat in beats:
        if not isinstance(beat.get('id'), str) or not beat['id'].strip() or beat['id'] in ids:
            raise ValueError('Beat IDs must be unique nonempty strings')
        ids.add(beat['id'])
        if not all(number(beat.get(k)) for k in ['start', 'end']):
            raise ValueError('Beat times must be finite numbers')
        if abs(beat['start'] - cursor) > .05 or beat['end'] <= beat['start']:
            raise ValueError('Beats must cover the video in order without gaps or overlaps')
        if beat.get('kind') not in ['mechanism', 'context', 'summary']:
            raise ValueError('Each beat needs kind mechanism, context, or summary')
        if beat['kind'] == 'mechanism':
            for key in ['object', 'before', 'action', 'after', 'meaning']:
                if not isinstance(beat.get(key), str) or not beat[key].strip():
                    raise ValueError(f'{beat["id"]}: missing {key}')
        cursor = beat['end']
    if abs(cursor - duration) > .15:
        raise ValueError('The plan must cover the full video duration')
    holds = sorted(plan.get('holds', []), key=lambda h: h['start'])
    previous_end = 0
    for hold in holds:
        if not all(number(hold.get(k)) for k in ['start', 'end']):
            raise ValueError('Hold times must be finite numbers')
        if not (0 <= hold['start'] < hold['end'] <= duration + .05) or hold['start'] < previous_end:
            raise ValueError('Holds must be in bounds and nonoverlapping')
        if not isinstance(hold.get('reason'), str) or not hold['reason'].strip():
            raise ValueError('Every reading hold needs a reason')
        kind = hold.get('kind')
        if kind not in ['read', 'final']:
            raise ValueError('Hold kind must be read or final')
        limit = 6 if kind == 'final' else 4
        if hold['end'] - hold['start'] > limit + .05:
            raise ValueError('Reading hold exceeds the production limit')
        if kind == 'final' and abs(hold['end'] - duration) > .15:
            raise ValueError('Final hold must reach the video end')
        previous_end = hold['end']
    hold_seconds = sum(h['end'] - h['start'] for h in holds)
    if hold_seconds > duration * .4:
        raise ValueError('Declared reading holds exceed 40% of the video')
    explained = sum(
        b['end'] - b['start'] - sum(overlap(b['start'], b['end'], h['start'], h['end']) for h in holds)
        for b in beats if b['kind'] == 'mechanism')
    if explained < (duration - hold_seconds) * .5:
        raise ValueError('Mechanism beats must cover at least half of non-hold time')
    return roi, beats, holds


def read_changes(video, stream, roi):
    width, height = stream['width'], stream['height']
    x, y, w, h = [round(n * size) for n, size in zip(roi, [width, height, width, height])]
    w, h = min(w, width - x), min(h, height - y)
    if w < 2 or h < 2:
        raise ValueError('Subject region is too small')
    sample_width = 160
    sample_height = max(2, round(sample_width * h / w))
    frame_bytes = sample_width * sample_height
    vf = f'crop={w}:{h}:{x}:{y}:exact=1,scale={sample_width}:{sample_height},fps={FPS},format=gray'
    changes = []
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            ['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1', '-filter_threads', '1',
             '-i', str(video), '-an', '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'],
            stdout=subprocess.PIPE, stderr=errors)
        try:
            previous = None
            index = 0
            while True:
                # Buffered read requests one complete frame or EOF.
                frame = process.stdout.read(frame_bytes)
                if not frame:
                    break
                if len(frame) != frame_bytes:
                    raise ValueError('Incomplete decoded frame')
                if previous is not None:
                    changed = sum(abs(a - b) >= CHANGE_THRESHOLD for a, b in zip(frame, previous))
                    changes.append(((index - .5) / FPS, changed / frame_bytes))
                previous = frame
                index += 1
            code = process.wait()
            if code:
                errors.seek(0)
                raise ValueError('ffmpeg decode failed: ' + errors.read(2000).decode(errors='replace'))
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.kill()
                process.wait()
    return changes


def measure_beat(beat, changes, holds):
    selected = [(t, ratio) for t, ratio in changes if beat['start'] <= t < beat['end']]
    flags = []
    longest_active = longest_hold = run_active = run_hold = 0
    for t, ratio in selected:
        if any(h['start'] <= t < h['end'] for h in holds):
            run_active = run_hold = 0
            continue
        active = ratio >= MIN_CHANGED_AREA
        flags.append(active)
        run_active = run_active + 1 if active else 0
        run_hold = run_hold + 1 if not active else 0
        longest_active = max(longest_active, run_active)
        longest_hold = max(longest_hold, run_hold)
    active_share = sum(flags) / len(flags) if flags else 0
    failures = []
    if not flags:
        failures.append('No evaluated subject frames in this beat')
    if longest_hold / FPS > MAX_UNEXPLAINED_HOLD_SECONDS + .05:
        failures.append('Subject needs a declared reading hold or a meaningful state change')
    if beat['kind'] == 'mechanism':
        if active_share < MIN_ACTIVE_SHARE:
            failures.append('Insufficient subject change across this mechanism beat')
        if longest_active / FPS + .00001 < MIN_CONTINUOUS_CHANGE_SECONDS:
            failures.append('Intermediate subject states were not detected for long enough')
    return {
        'id': beat['id'], 'kind': beat['kind'], 'evaluated_transitions': len(flags),
        'active_share': round(active_share, 4),
        'longest_continuous_change_seconds': longest_active / FPS,
        'longest_undeclared_hold_seconds': longest_hold / FPS,
        'failures': failures,
    }


def validate_review(review, sha, beats):
    failures = []
    if review.get('video_sha256') != sha:
        failures.append('Semantic review does not match the final video SHA-256')
    if review.get('method') not in ['video', 'frame_sequence']:
        failures.append('Review method must be video or frame_sequence')
    checks = review.get('checks', [])
    ids = [c.get('beat_id') for c in checks]
    if len(ids) != len(set(ids)):
        failures.append('Semantic review contains duplicate beat IDs')
    wanted = {b['id'] for b in beats if b['kind'] == 'mechanism'}
    if set(ids) != wanted:
        failures.append('Semantic review must cover exactly the mechanism beats')
    by_id = {b['id']: b for b in beats}
    for check in checks:
        beat = by_id.get(check.get('beat_id'))
        if beat is None:
            continue
        if check.get('explains_mechanism') is not True:
            failures.append(f'{beat["id"]}: subject change and explanation not confirmed')
        for key in ['observed_object', 'observed_change', 'meaning']:
            if not isinstance(check.get(key), str) or not check[key].strip():
                failures.append(f'{beat["id"]}: missing semantic evidence {key}')
        times = check.get('evidence_times', [])
        if (not isinstance(times, list) or len(times) < 3 or not all(number(t) for t in times)
                or times != sorted(set(times))
                or not all(beat['start'] <= t <= beat['end'] for t in times)):
            failures.append(f'{beat["id"]}: at least three ordered in-beat evidence times required')
    return failures


def audit(video, plan, review=None, mechanical_only=False):
    meta = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)]))
    stream = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    duration = float(stream.get('duration', meta['format']['duration']))
    if not 0 < duration <= 600:
        raise ValueError('Expected a short video between 0 and 600 seconds')
    roi, beats, holds = validate_plan(plan, duration)
    changes = read_changes(video, stream, roi)
    if len(changes) < max(1, int(duration * FPS) - 3):
        raise ValueError('Decoded samples do not cover the full video')
    results = [measure_beat(b, changes, holds) for b in beats]
    failures = [f'{b["id"]}: {f}' for b in results for f in b['failures']]
    sha = hashlib.sha256(video.read_bytes()).hexdigest()
    semantic = 'not_reviewed'
    if review is not None:
        review_failures = validate_review(review, sha, beats)
        failures.extend(review_failures)
        semantic = 'failed' if review_failures else 'passed'
    if failures:
        status, code = 'FAIL', 1
    elif semantic == 'passed':
        status, code = 'PASS', 0
    else:
        status, code = 'REVIEW_REQUIRED', 0 if mechanical_only else 2
    report = {
        'status': status, 'video_sha256': sha, 'duration_seconds': duration,
        'roi': roi, 'mechanical_check': 'failed' if any(b['failures'] for b in results) else 'passed',
        'semantic_review': semantic,
        'thresholds': {'sample_fps': FPS, 'pixel_change_threshold': CHANGE_THRESHOLD,
                       'min_changed_area': MIN_CHANGED_AREA, 'min_active_share': MIN_ACTIVE_SHARE,
                       'min_continuous_change_seconds': MIN_CONTINUOUS_CHANGE_SECONDS,
                       'max_undeclared_hold_seconds': MAX_UNEXPLAINED_HOLD_SECONDS},
        'beats': results, 'failures': failures,
        'limitation': 'Measurements show temporal pixel changes; semantic evidence requires actual review.',
    }
    return report, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--review', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mechanical-only', action='store_true')
    args = parser.parse_args()
    try:
        report, code = audit(args.video, json.loads(args.plan.read_text()),
                             json.loads(args.review.read_text()) if args.review else None,
                             args.mechanical_only)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, subprocess.SubprocessError) as exc:
        report, code = {'status': 'FAIL', 'failures': [str(exc)]}, 1
    output = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    print(output, end='')
    return code


if __name__ == '__main__':
    sys.exit(main())
