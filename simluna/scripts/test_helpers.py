#!/usr/bin/env python3
"""Regression tests for false-success detection and macro isolation."""
import tempfile
from pathlib import Path
import unittest
from run_checked import prepare, assess

MACRO = '/run/initialize\n/analysis/filename /workdir/rootfiles/SimLUNA.root\n/run/beamOn 1000000\n'


class Checks(unittest.TestCase):
    def test_explicit_seed_and_local_output(self):
        result = prepare(MACRO, 12, [11, 23])
        self.assertIn('/analysis/filename result.root', result)
        self.assertLess(result.index('/random/setSeeds 11 23'), result.index('/run/beamOn 12'))
        self.assertNotIn('/workdir/', result)

    def test_hidden_or_multiple_runs_rejected(self):
        for x in [MACRO + '/run/beamOn 3', '/control/execute other.mac\n' + MACRO,
                  MACRO.replace('/run/initialize', ''), MACRO + '/control/loop x.mac i 1 10']:
            with self.assertRaises(ValueError):
                prepare(x, 12, [11, 23])

    def test_zero_status_is_not_success(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'result.root'
            out.write_bytes(b'root' + bytes(200))
            self.assertTrue(assess('***** COMMAND NOT FOUND </bad> *****', 0, 12, out))
            self.assertTrue(assess('Number of events: 11', 0, 12, out))
            self.assertTrue(assess('Number of events: 12\nOverlap is detected', 0, 12, out))
            self.assertFalse(assess('Number of events: 12', 0, 12, out))
            out.unlink()
            self.assertTrue(assess('Number of events: 12', 0, 12, out))


if __name__ == '__main__':
    unittest.main()
