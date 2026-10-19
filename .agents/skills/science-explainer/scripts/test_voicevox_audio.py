"""Exercise speaker selection, API requests, cache invalidation and render provenance."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, urlsplit
import wave

import voicevox_audio as audio


class VoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = []
        cls.style = 14
        cls.available = True
        cls.version = '0.25.2'

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                path = urlsplit(self.path).path
                if path == '/version':
                    value = cls.version
                elif path == '/speakers':
                    value = [dict(name='青山龍星', speaker_uuid='other',
                                  styles=[dict(name='ノーマル', id=13)])]
                    if cls.available:
                        value.append(dict(name=audio.choice()['name'],
                            speaker_uuid=audio.choice()['speaker_uuid'],
                            styles=[dict(name='ノーマル', id=cls.style)]))
                else:
                    value = {'policy': 'Test policy'}
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())

            def do_POST(self):
                url = urlsplit(self.path)
                body = self.rfile.read(int(self.headers['Content-Length']))
                cls.requests.append((url.path, parse_qs(url.query), body))
                if url.path == '/audio_query':
                    data = json.dumps({'accent_phrases': []}).encode()
                else:
                    out = io.BytesIO()
                    with wave.open(out, 'wb') as stream:
                        stream.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
                        stream.writeframes(b'\x01\x00'*4800)
                    data = out.getvalue()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(data)

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.api = 'http://127.0.0.1:'+str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        type(self).requests.clear()
        type(self).style, type(self).available, type(self).version = 14, True, '0.25.2'
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        audio.write_json(self.root/'story.json', [{'id': 'intro', 'say': '設定した話者で読みます。'}])

    def prepare(self):
        return audio.prepare_story(self.root, api=self.api)

    def test_default_used_for_query_and_synthesis_and_credit(self):
        voice = self.prepare()
        self.assertEqual([r[1]['speaker'] for r in self.requests], [['14'], ['14']])
        self.assertEqual(voice['name'], '冥鳴ひまり')
        self.assertEqual(voice['credit'], 'VOICEVOX:冥鳴ひまり')
        self.assertEqual(audio.verify_project(self.root), voice)

    def test_resolves_name_and_uuid_with_live_style_id(self):
        type(self).style = 314
        voice = self.prepare()
        self.assertEqual(voice['style'], 314)
        self.assertTrue(all(r[1]['speaker'] == ['314'] for r in self.requests))

    def test_missing_selected_speaker_fails_before_synthesis(self):
        type(self).available = False
        with self.assertRaisesRegex(RuntimeError, 'unavailable'):
            self.prepare()
        self.assertEqual(self.requests, [])

    def test_legacy_cache_replaced_and_matching_cache_reused(self):
        wav = self.root/'audio/00-intro.wav'
        wav.parent.mkdir()
        wav.write_bytes(b'old voice')
        wav.with_suffix('.sha256').write_text('legacy style 13')
        self.prepare()
        self.assertEqual(len(self.requests), 2)
        self.prepare()
        self.assertEqual(len(self.requests), 2)
        wav.write_bytes(b'changed voice')
        self.prepare()
        self.assertEqual(len(self.requests), 4)

    def test_version_settings_and_query_changes_invalidate_cache(self):
        self.prepare()
        type(self).version = 'next-version'
        self.prepare()
        self.assertEqual(len(self.requests), 4)
        wav = self.root/'audio/00-intro.wav'
        engine = audio.Voicevox(api=self.api, settings={'speedScale': 1.2})
        engine.synthesize('設定した話者で読みます。', wav)
        self.assertEqual(len(self.requests), 6)
        wav.with_suffix('.query.json').write_text('{}')
        engine.synthesize('設定した話者で読みます。', wav)
        self.assertEqual(len(self.requests), 8)

    def test_legacy_voice_and_changed_story_block_render(self):
        voice = self.prepare()
        audio.write_json(self.root/'assets/voice.json', {**voice, 'name': '青山龍星'})
        with self.assertRaisesRegex(ValueError, 'Narrator differs'):
            audio.verify_project(self.root)
        audio.write_json(self.root/'assets/voice.json', voice)
        audio.write_json(self.root/'story.json', [{'id': 'intro', 'say': '別の原稿'}])
        with self.assertRaisesRegex(ValueError, 'story changed'):
            audio.verify_project(self.root)

    def test_render_receipt_rejects_changed_video_or_audio(self):
        self.prepare()
        video = self.root/'render.mp4'
        video.write_bytes(b'render fixture')
        inputs = audio.render_inputs(self.root)
        with self.assertRaisesRegex(ValueError, 'no narration receipt'):
            audio.verify_render(self.root, video)
        audio.save_render(self.root, video, inputs)
        audio.verify_render(self.root, video)
        video.write_bytes(b'older render')
        with self.assertRaisesRegex(ValueError, 'Render differs'):
            audio.verify_render(self.root, video)
        (self.root/'audio/00-intro.wav').write_bytes(b'another voice')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            audio.verify_project(self.root)

    def test_combined_narration_hash_is_verified(self):
        self.prepare()
        combined = self.root/'audio/narration.wav'
        combined.write_bytes((self.root/'audio/00-intro.wav').read_bytes())
        engine = audio.Voicevox(api=self.api)
        voice = json.loads((self.root/'assets/voice.json').read_text())
        engine.save_project(self.root, voice['records'], ['audio/narration.wav'])
        audio.verify_project(self.root)
        combined.write_bytes(b'wrong combined audio')
        with self.assertRaisesRegex(ValueError, 'Combined narration'):
            audio.verify_project(self.root)


if __name__ == '__main__':
    unittest.main()
