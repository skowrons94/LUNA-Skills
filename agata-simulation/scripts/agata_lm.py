"""List-mode output (GammaEvents.NNNN) of the AGATA Geant4 code -> compact numpy archives.

Text format (OUTPUT_MASK 111001000): header ends with a "$" line; each event starts with
"-100 <evnum>", followed by "-101" (emitter velocity), "-102" (emitter position) and "-1 E ux uy uz k"
(each emitted gamma, lab frame) lines, then one line per (packed) interaction point:
"<det> <Edep keV> <x> <y> <z> <segcode>" (mm). AGATA crystals have det < 1000; segcode is the
two-digit sector*10 + slice code of the 36-fold segmentation (6 sectors x 6 slices).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def convert_lm(path: Path, out: Path) -> int:
    """Parse one list-mode file and save hits and emitted gammas to `out` (npz). Returns n events."""
    hev, hdet, hseg, he, hx, hy, hz = [], [], [], [], [], [], []
    gev, ge, gu = [], [], []
    ev = -1
    n = 0
    with open(path) as fh:
        for line in fh:
            if line.startswith("$"):
                break
        for line in fh:
            s = line.split()
            if not s:
                continue
            tag = int(s[0])
            if tag == -100:
                n += 1
                ev = n - 1
            elif tag == -1:
                gev.append(ev)
                ge.append(float(s[1]))
                gu.append((float(s[2]), float(s[3]), float(s[4])))
            elif 0 <= tag < 1000:
                hev.append(ev)
                hdet.append(tag)
                he.append(float(s[1]))
                hx.append(float(s[2]))
                hy.append(float(s[3]))
                hz.append(float(s[4]))
                code = int(s[5])
                hseg.append((code // 10) * 6 + code % 10)  # 0..35
    # pack Geant4 steps: one energy-weighted point per (event, crystal, segment)
    ev, det, seg = np.asarray(hev, np.int64), np.asarray(hdet, np.int64), np.asarray(hseg, np.int64)
    e = np.asarray(he, float)
    xyz = np.c_[hx, hy, hz].astype(float).reshape(-1, 3)
    key = (ev * 1000 + det) * 36 + seg
    o = np.argsort(key, kind="stable")
    uk, first = np.unique(key[o], return_index=True)
    pe = np.add.reduceat(e[o], first) if len(first) else np.zeros(0)
    pxyz = (np.add.reduceat(xyz[o] * e[o][:, None], first) / np.maximum(pe, 1e-12)[:, None]) if len(first) else np.zeros((0, 3))
    np.savez_compressed(
        out,
        n_events=np.int64(n),
        event=(uk // 36 // 1000).astype(np.int32), det=(uk // 36 % 1000).astype(np.int16),
        seg=(uk % 36).astype(np.int16), e=pe.astype(np.float32),
        x=pxyz[:, 0].astype(np.float32), y=pxyz[:, 1].astype(np.float32), z=pxyz[:, 2].astype(np.float32),
        g_event=np.asarray(gev, np.int32), g_e=np.asarray(ge, np.float32),
        g_u=np.asarray(gu, np.float32).reshape(-1, 3),
    )
    return n


def load(path: Path) -> dict:
    """Packed hits (one point per event/crystal/segment) and emitted gammas of one run."""
    with np.load(path) as f:
        return {k: f[k] for k in f.files}
