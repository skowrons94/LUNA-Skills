#!/usr/bin/env python3
"""Inspect local BGO Tree1 with PyROOT; energies are keV in the verified variant."""
import argparse
import json
import math
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--expected-entries', type=int, help='Use only for AllEventFlag=true')
    p.add_argument('--require-hits', action='store_true')
    a = p.parse_args()
    import ROOT
    ROOT.gROOT.SetBatch(True)
    f = ROOT.TFile.Open(str(a.file.resolve()), 'READ')
    if not f or f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered):
        raise RuntimeError('Missing, corrupt, or recovered ROOT file')
    t = f.Get('Tree1')
    if not t or not t.InheritsFrom('TTree'):
        raise RuntimeError('Expected Tree1 TTree; inspect AnalysisManager for other variants')
    names = [b.GetName() for b in t.GetListOfBranches()]
    report = {'file': str(a.file.resolve()), 'entries': t.GetEntries(), 'branches': names}
    errors = []
    if a.expected_entries is not None and t.GetEntries() != a.expected_entries:
        errors.append('Entry count differs from expected generated event count')
    if 'Edep' in names:
        hit = invalid = peak = 0
        maximum = 0.0
        for event in t:
            e = [float(x) for x in event.Edep]
            if not e or any(not math.isfinite(x) or x < 0 for x in e):
                invalid += 1
                continue
            total = sum(e)
            hit += total > 0
            peak += 655 <= total <= 668
            maximum = max(maximum, total)
        report.update(events_with_energy=hit, invalid_energy_events=invalid,
                      max_sum_keV=maximum, sum_window_655_668_keV=peak)
        if invalid:
            errors.append('Non-finite, negative or empty deposited energies')
        if a.require_hits and not hit:
            errors.append('No deposited energy')
    elif a.require_hits:
        errors.append('Edep missing')
    f.Close()
    report['errors'] = errors
    print(json.dumps(report, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
