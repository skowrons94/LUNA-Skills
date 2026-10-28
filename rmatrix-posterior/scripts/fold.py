"""Exact sign symmetry of R-matrix levels: fold posterior draws before diagnostics.

Changing the sign of every reduced-width amplitude of one level (particle and photon
channels) leaves the R matrix, the level matrix and the internal capture amplitude
unchanged, so the posterior has exact mirror copies.  A chain stays in the copy it
starts in; pooled with chains in another copy it gives a large R-hat although nothing
physical differs.  Fold each draw to the sign of the level's largest width at a
reference point (the MAP) before computing R-hat or ESS.
"""
import numpy as np


def level_width_groups(m):
    """Free indices of all widths of each level, from a pyazr ``azure2`` model."""
    groups = {}
    for p in m.parameters.widths:
        if not p.fixed and p.free_index is not None:
            groups.setdefault((p.jgroup, p.level), []).append(p.free_index)
    return list(groups.values())


def fold_level_signs(X, groups, x_ref):
    """Map draws X (..., n) to the sign convention of x_ref, level by level.

    For each level the reference channel is its largest |width| at x_ref; a draw in
    which that width has the other sign has every width of the level negated.
    Returns the folded copy and the number of (draw, level) flips."""
    X = np.array(X, float, copy=True)
    flips = 0
    for idx in groups:
        k = idx[int(np.argmax(np.abs(x_ref[idx])))]
        flip = np.sign(X[..., k]) != np.sign(x_ref[k])
        flips += int(np.sum(flip))
        for i in idx:
            X[..., i] = np.where(flip, -X[..., i], X[..., i])
    return X, flips
