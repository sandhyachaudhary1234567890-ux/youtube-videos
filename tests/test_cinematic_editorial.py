import json
import math
import tempfile
import unittest
import wave
from collections import Counter
from pathlib import Path
import numpy as np
from scripts import render_master_video_60fps as renderer
from scripts.cinematic_editorial import sound_cues, synthesize_soundtrack, SAMPLE_RATE

class EditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(Path('videos/timeline_manifest.json').read_text())
        cls.shots = renderer.build_shot_schedule(cls.manifest)
        cls.safe = next(p for p in cls.manifest['placements'] if p['silence_zone'])

    def test_deterministic_schedule_and_coverage(self):
        self.assertEqual(self.shots, renderer.build_shot_schedule(self.manifest))
        for p in self.manifest['placements']:
            shots = [s for s in self.shots if s['seg_id']==p['id']]
            self.assertAlmostEqual(sum(s['duration'] for s in shots), p['duration'], delta=.002)
            self.assertAlmostEqual(shots[-1]['end'],p['end'],places=5)

    def test_selective_not_constant_transitions(self):
        counts=Counter(s['trans_type'] for s in self.shots)
        self.assertGreater(counts['cut'], len(self.shots)*.5)
        for s in self.shots:
            if s['seg_id']==self.safe['id']:
                self.assertEqual(s['env'],'none')
                self.assertEqual(s['trans_type'],'fade')

    def test_sparse_cues_and_safe_zone(self):
        cues=sound_cues(self.shots,self.manifest)
        self.assertGreater(len(cues),0)
        for i,c in enumerate(cues):
            self.assertFalse(self.safe['start']-1<=c['time']<=self.safe['end']+1)
            if i: self.assertGreaterEqual(c['time']-cues[i-1]['time'],5.999)
            self.assertLessEqual(c['gain_db'],-29)

    def test_pcm_silence_after_all_tails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fx.wav'
            synthesize_soundtrack(self.shots,self.manifest,p)
            with wave.open(str(p)) as f:
                self.assertEqual(f.getnframes(),600*SAMPLE_RATE)
                f.setpos(math.floor(self.safe['start']*SAMPLE_RATE))
                data=np.frombuffer(f.readframes(math.ceil(self.safe['end']*SAMPLE_RATE)-f.tell()),dtype='<i2')
                self.assertEqual(np.max(np.abs(data)),0)

if __name__ == '__main__': unittest.main()
