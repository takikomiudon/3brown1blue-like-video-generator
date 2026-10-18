#!/usr/bin/env python3
"""Check durable knowledge, upstream copies and delivered video without rendering."""
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    required_docs = (
        'KNOWLEDGE research fact-check credits production-workflow storyboard '
        'validation quality-upgrade quality-upgrade-pilot quality-upgrade-source-links '
        'shorts-topic-research platform-duration-notes troubleshooting '
        'preservation-and-delivery restoration'
    ).split()
    own_files = [ROOT / 'README.md', ROOT / 'AGENTS.md',
                 ROOT / 'shorts/decay-heat/README.md',
                 ROOT / 'shorts/decay-heat/plan.md',
                 ROOT / '.agents/skills/science-explainer/SKILL.md']
    own_files += [ROOT / 'docs' / (name + '.md') for name in required_docs]
    for path in own_files:
        require(path.is_file(), f'Missing document: {path.relative_to(ROOT)}')
        if not path.is_file():
            continue
        # Ignore fenced examples; validate actual project Markdown links.
        body = re.sub(r'^```.*?^```[^\n]*$', '', path.read_text(), flags=re.M | re.S)
        for target in re.findall(r'\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', body):
            target = target.strip('<>')
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            local = unquote(target.split('#', 1)[0].split('?', 1)[0])
            require((path.parent / local).exists(),
                    f'Broken link: {path.relative_to(ROOT)} -> {target}')

    skills = ['science-explainer', 'manim-video', 'manim-composer',
              'manimce-best-practices', 'remotion-best-practices']
    for name in skills:
        path = ROOT / '.agents/skills' / name / 'SKILL.md'
        require(path.is_file(), f'Missing skill: {name}')
        if path.is_file():
            content = path.read_text()
            match = re.match(r'^---\s*\n(.*?)\n---', content, flags=re.S)
            require(bool(match), f'Missing frontmatter: {name}')
            if match:
                for field in ['name', 'description']:
                    require(bool(re.search(rf'^{field}:\s*\S', match[1], flags=re.M)),
                            f'Missing {field}: {name}')

    manifest = json.loads((ROOT / 'docs/vendor-skills.json').read_text())
    paths = set()
    for item in manifest['files']:
        path = ROOT / item['path']
        require(item['path'] not in paths, f'Duplicate vendor path: {item["path"]}')
        paths.add(item['path'])
        require(path.is_file(), f'Missing vendor file: {item["path"]}')
        if path.is_file():
            require(digest(path) == item['sha256'], f'Vendor hash mismatch: {item["path"]}')
    require(len(paths) == 223, f'Expected 223 upstream files, found {len(paths)}')
    for item in manifest['sources']:
        require(bool(re.fullmatch('[0-9a-f]{40}', item['commit'])),
                f'Invalid upstream commit: {item["skill"]}')
    actual_vendor = {str(path.relative_to(ROOT))
                     for name in skills[1:]
                     for path in (ROOT / '.agents/skills' / name).rglob('*')
                     if path.is_file()}
    require(actual_vendor == paths, 'Vendor inventory differs from manifest')

    sources = json.loads((ROOT / 'docs/sources.json').read_text())
    require(len(sources) == 15, 'Expected 15 source records')
    require(sources == json.loads((ROOT / 'docs/quality-upgrade-sources.json').read_text()),
            'Source metadata copies differ')
    for item in sources:
        require(item['read_operation'] == 'passed', f'Source not verified: {item["repository"]}')
        require(bool(re.fullmatch('[0-9a-f]{40}', item['head_verified_on_restoration'])),
                f'Invalid source HEAD: {item["repository"]}')

    outputs = ROOT / 'shorts/decay-heat/outputs'
    validation = json.loads((outputs / 'validation.json').read_text())
    video = outputs / validation['file']
    require(video.is_file(), 'Missing delivered 1080p video')
    if video.is_file():
        require(video.stat().st_size == validation['size_bytes'], 'Video size mismatch')
        require(digest(video) == validation['sha256'], 'Video hash mismatch')
    fallback = outputs / 'decay-heat-short-ja-720p.mp4'
    require(fallback.is_file() and fallback.stat().st_size == 2482581,
            'Missing or changed 720p delivery')
    if errors:
        for error in errors:
            print('FAIL:', error, file=sys.stderr)
        return 1
    print(f'PASS: {len(own_files)} project documents, {len(skills)} skill entry points, '
          f'{len(paths)} upstream file hashes, {len(sources)} sources, delivered MP4 integrity.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
