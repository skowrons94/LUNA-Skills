# Editing the model

## Editing the model: adding and removing levels

AZURE2 reads its model from the file, so an edited scheme is applied by
**writing a new `.azr` and launching a fresh instance from it**. `AzrModel`
parses only the `<levels>` block and re-emits everything else verbatim; the
original file is never modified.

```python
from pyazr import AzrModel, azure2

mdl = AzrModel.from_file("7Be.azr")
print(mdl)                                        # J^pi / energies / channels / fixed flags
mdl.find(jpi="5/2+", energy=10.253, tol=2e-2)     # -> [AzrLevel]

mdl.remove_level(jpi="1/2+", energy=20)           # drop a background pole entirely
mdl.add_level(J=1.5, parity=+1, energy=8.6,       # add a 3/2+ resonance
              channels=[dict(pair=1, L=2, S=0.5, gamma=1000.0, fixed=False),
                        dict(pair=2, L=1, S=0.5, gamma=0.1)],
              level_fixed=False)                  # level_fixed=False -> energy is a fit parameter
mdl.deactivate_level(jpi="7/2-", energy=4.572)    # keep in file, zero+fix every gamma
path = mdl.write("_test.azr")

with azure2(path, cwd=HERE) as m:
    ...
```

Rules that will bite you:

- **All levels of one J^π share one channel set** (an R-matrix J-group
  requirement). If a level of that `(J, parity)` already exists, `add_level`
  clones that group's exact channel structure and applies your `gamma`/`fixed`
  only to matching `(pair, L, S)`; unmentioned channels are added inert
  (`gamma=0`, fixed). A spec matching none of them raises and lists the allowed
  channels. Only for a brand-new J^π do your channels define the group.
- For the same reason `remove_channel(jpi, pair, L, S)` removes that channel
  from **every level of the group**; removing it from one level makes AZURE2
  reject the file.
- `add_level`/`add_channel` can only reference a **pair that already exists**
  in the file — new particle pairs must be added in the GUI.
- `gamma` in the file is the **reduced width / ANC input**, not the eV partial
  width the GUI shows. Seed a new channel with a small nonzero value (fits from
  exactly 0 have zero gradient) and set `fixed=False` to free it.
- Levels are renumbered (`levelID`) automatically on every edit.

**Removing a level: file-level vs runtime.** Two different tools:

| | effect | use for |
|---|---|---|
| `AzrModel.remove_level` | level gone from the file; parameter vector shrinks | a persisted reduced model to refit |
| `AzrModel.deactivate_level` | stays in the file, all γ = 0 and fixed | persisted "level off" that keeps the J-group's channel set |
| `azure2.without_level(x, ...)` | returns a copy of `x` with that level's free reduced widths zeroed | *frozen* Δχ² probes, no refit, same parameter vector |
| `azure2.only_level(x, ...)` | zeroes every *other* level's widths | the bare contribution of one resonance |

Zeroing reduced widths decouples a level from every channel, so it contributes
exactly nothing — provided its *fixed* widths are already zero (check with
`m.parameters.widths`; in the 7Be model all fixed widths are 0).

Other `.azr` edits without touching the GUI:

```python
mdl.channel_radii()                                      # {pair: radius fm}
mdl.set_channel_radius(1, 5.0)                           # 3He+alpha, all its lines
mdl.set_segment_norm("Toth", vary=True, sys_error=8.0)   # percent, as stored
mdl.set_segment_active("Spiger", False)                  # drop a dataset from the fit
mdl.set_segment_datafile("Elwyn-F0012002", "data/new.dat")
mdl.set_extrapolations([...]) / add_extrapolation(...) / clear_extrapolations()
mdl.apply_fit(m.parameters, x_best, transform=m.transform_rwa)   # fit -> <levels>
```

`apply_fit` turns a fit result into a real `.azr` snapshot — the reference to
reuse and hand to the GUI. Matching is by (2J, parity, input energy, pair/L/S).

**The `<levels>` `gamma` field is NOT a reduced-width amplitude.** It holds the
physical value `parameters.out` prints: Γ in **eV** for an open particle
channel, an **ANC in fm^-1/2** for a closed (sub-threshold) one, Γ_γ in eV for a
photon channel — i.e. exactly `transform_rwa(x)`. In the 7Be model the two
differ by factors of 10² to 10⁷, and a file written with the rwa loads without
complaint and is wrong. So `apply_fit` requires the conversion to be explicit —
`transform=m.transform_rwa`, or `physical=True` if you converted already — and
raises if given neither. Level energies need no conversion.

`apply_fit` covers `<levels>` only: normalizations do not live there, so a fit
that moved them needs its `param.sav` alongside. Verify a written file by
reloading it and comparing `transform_rwa(m.params_rwa)` against the fit's
physical vector — every R-matrix entry must match.

`pyazr/examples/save_fit_to_azr.py` does the whole thing — loads a fit from
`param.sav` or an `.npz`, optionally re-radiuses it (`--radius 1=4.70`, dropping
the stale `intEC` caches), writes the `.azr` plus a companion `param.sav` with
the norms, and fails loudly if the result does not round-trip.

### Defining extrapolation grids

```python
mdl.set_extrapolations([
    dict(entrance=1, exit=-1, e_min=0.10/cm2lab, e_max=8.5/cm2lab,
         e_step=0.05/cm2lab, observable="total-capture"),
    dict(entrance=1, exit=1, e_min=0.05, e_max=6.0, e_step=0.05,
         observable="differential-cm", angle=90.0),
])
```

`exit=-1` means summed/total (capture). `observable` ∈ `angle-integrated`,
`differential`, `differential-cm`, `total-capture`, `angular-distribution`
(needs `order=`), `phase-shift` (needs `phase_J=`, `phase_L=`). Energies are
**lab** (`cm2lab = m_target/(m_beam+m_target)`; ³He+α 0.5703, p+⁶Li 0.8565 —
divide c.m. by it). Remember to delete `output/intEC.extrap` afterwards.

Note the `isDiff` codes differ between the two blocks: in `<segmentsData>` 3 is
total-capture and 4 is differential-cm; in `<segmentsTest>` 3 is angular
distribution, 4 total-capture, 5 differential-cm. pyazr handles this — hand-edits
must not.
