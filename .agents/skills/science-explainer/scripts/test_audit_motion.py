#!/usr/bin/env python3
"""Integration regressions with generated subject trajectories; no network or TTS."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('audit_motion.py')
spec = importlib.util.spec_from_file_location('audit_motion', SCRIPT)
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)


class SubjectMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='subject-motion-')
        cls.root = Path(cls.temp.name)
        cls.files = {}
        for case in ['a', 'b', 'c', 'd', 'e', 'f']:
            frames = bytearray()
            for i in range(40):
                level = 25 + (i % 6) * 35 if case == 'e' else 25
                frame = bytearray([level]) * (160 * 160)
                x = 20 + (i * 2 if case == 'd' else (i // 10) * 20 if case == 'c' else 0)
                width = 12 + i // 2 if case == 'f' else 20
                height = 10 + i if case == 'f' else 30
                for y in range(45, 45 + height):
                    frame[y * 160 + x:y * 160 + x + width] = bytes([230]) * width
                if case == 'b':
                    x2 = 10 + i * 2
                    for y in range(140, 153):
                        frame[y * 160 + x2:y * 160 + x2 + 20] = bytes([230]) * 20
                frames.extend(frame)
            path = cls.root / f'{case}.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray',
                            '-s', '160x160', '-r', '10', '-i', 'pipe:0', '-an',
                            '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p', str(path)],
                           input=frames, check=True)
            cls.files[case] = path

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def plan(self):
        return {'roi': [0, 0, 1, .75], 'beats': [
            {'id': 'travel', 'kind': 'mechanism', 'start': 0, 'end': 4,
             'object': 'subject', 'before': 'x=20', 'action': 'x increases with time',
             'after': 'x=98', 'meaning': 'position changes at a constant rate'}], 'holds': []}

    def review(self, case='d', confirms=True):
        return {'video_sha256': hashlib.sha256(self.files[case].read_bytes()).hexdigest(),
                'method': 'frame_sequence', 'checks': [
                    {'beat_id': 'travel', 'observed_object': 'subject',
                     'observed_change': 'increasing x coordinate',
                     'meaning': 'position changes at a constant rate',
                     'evidence_times': [.5, 1, 1.5], 'explains_mechanism': confirms}]}

    def test_subject_requires_temporal_change(self):
        report, code = motion.audit(self.files['a'], self.plan())
        self.assertEqual(code, 1)
        self.assertEqual(report['mechanical_check'], 'failed')

    def test_changes_outside_declared_subject_region_do_not_count(self):
        report, code = motion.audit(self.files['b'], self.plan())
        self.assertEqual(code, 1)
        self.assertLess(report['beats'][0]['active_share'], .12)

    def test_intermediate_states_required(self):
        report, code = motion.audit(self.files['c'], self.plan())
        self.assertEqual(code, 1)
        self.assertLess(report['beats'][0]['longest_continuous_change_seconds'], .3)

    def test_continuous_subject_change_still_requires_review(self):
        report, code = motion.audit(self.files['d'], self.plan())
        self.assertEqual(code, 2)
        self.assertEqual(report['status'], 'REVIEW_REQUIRED')
        self.assertEqual(report['mechanical_check'], 'passed')

    def test_diagnostic_mode_preserves_review_required_status(self):
        report, code = motion.audit(self.files['d'], self.plan(), mechanical_only=True)
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'REVIEW_REQUIRED')

    def test_motion_and_confirmed_meaning_pass(self):
        report, code = motion.audit(self.files['d'], self.plan(), self.review())
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'PASS')

    def test_geometric_change_is_supported(self):
        plan, review = self.plan(), self.review('f')
        plan['beats'][0].update(before='small area', action='width and height increase',
                                after='larger area', meaning='area increases with dimensions')
        review['checks'][0].update(observed_change='width and height increase',
                                   meaning='area increases with dimensions')
        report, code = motion.audit(self.files['f'], plan, review)
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'PASS')

    def test_pixel_changes_do_not_establish_meaning(self):
        report, code = motion.audit(self.files['e'], self.plan(), self.review('e', False))
        self.assertEqual(report['mechanical_check'], 'passed')
        self.assertEqual(code, 1)
        self.assertEqual(report['semantic_review'], 'failed')

    def test_review_must_match_video(self):
        report, code = motion.audit(self.files['d'], self.plan(), self.review('a'))
        self.assertEqual(code, 1)
        self.assertIn('SHA-256', ' '.join(report['failures']))

    def test_review_must_cover_mechanism_beats(self):
        review = self.review()
        review['checks'] = []
        report, code = motion.audit(self.files['d'], self.plan(), review)
        self.assertEqual(code, 1)

    def test_plan_covers_full_duration(self):
        plan = self.plan()
        plan['beats'][0]['end'] = 2
        with self.assertRaises(ValueError):
            motion.audit(self.files['d'], plan)

    def test_reading_time_has_a_bound(self):
        plan = self.plan()
        plan['holds'] = [{'start': 0, 'end': 4, 'kind': 'final', 'reason': 'read result'}]
        with self.assertRaises(ValueError):
            motion.audit(self.files['d'], plan)

    def test_mechanism_time_is_required(self):
        plan = self.plan()
        plan['beats'][0]['kind'] = 'context'
        with self.assertRaises(ValueError):
            motion.audit(self.files['d'], plan)

    def test_cli_review_required_exit_code_and_saved_report(self):
        plan_path, out = self.root / 'plan.json', self.root / 'report.json'
        plan_path.write_text(json.dumps(self.plan()))
        process = subprocess.run([sys.executable, str(SCRIPT), str(self.files['d']),
                                  '--plan', str(plan_path), '--output', str(out)], capture_output=True)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(json.loads(out.read_text())['status'], 'REVIEW_REQUIRED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
