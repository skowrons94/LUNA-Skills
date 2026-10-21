# Trojan Horse (THM) segments

The modified R-matrix / half-off-shell path. A THM measurement induces the
reaction with a nucleon bound inside a carrier nucleus, so it proceeds below the
Coulomb barrier without penetrability suppression, and what is extracted is
half-off-shell: entrance off the energy shell, exit on it.

**A THM segment adds 10 to its observable code.** THM is orthogonal to the
observable, so `isDiff >= 10` means THM and `isDiff - 10` is the ordinary code:
`10` = THM angle-integrated, `11` = THM differential. `ESegment` strips the
offset before anything else looks at it, so THM composes with every observable
including the analyzing power.

```python
for s in m.datasets:
    print(s.observable, s.thm)      # e.g. 'angle-integrated' True
print(m.datasets.table())           # marks such segments "[THM]"
```

**The analytic gradient does not cover THM.** The adjoint differentiates the
T-matrix observable, not the half-off-shell one, so THM segments are excluded
from the analytic accumulation and their contribution to the energy, width and
norm derivatives comes from central differences instead (`AZURECalc::Gradient`,
guarded by `haveTHM`). Everything else stays analytic.

**Widths may be reduced width amplitudes.** A channel line can carry
`gammaIsRWA`, in which case its `gamma` column is an amplitude in MeV^(1/2)
rather than a partial width in eV or an ANC — useful when a level is known only
from a THM measurement. AZURE2 keeps the convention on output too
(`CNuc::GetTransformParams` returns the amplitude unchanged for such a channel),
so a fit written back never flips it.

```python
ch.gamma_is_rwa            # AzrChannel: is this channel's gamma an amplitude?
w.input_is_rwa             # Parameter: same thing, from the live API
p.binding_energy           # Pair: THM binding energy (MeV), 0 if not THM
```

Two traps:

- **Never convert an rwa-declared width.** `apply_fit(..., transform=...)` is
  safe because the transform respects the flag, but hand-rolled rwa->physical
  arithmetic will corrupt the file by orders of magnitude.
- **`Parameter.wigner_limit` is `gamma^2_W` in MeV**, the limit on the reduced
  width *squared*. It matches neither convention `value` can be in. Use
  `pyazr.widths` to form theta^2 rather than dividing by it.

Reference case: `tests/17O` — 17O(n,alpha)14C from Guardo/Sergi *et al.*,
23 points, one THM segment, chi-squared 12.3193. It is the only case in the
suite that touches this path, and it exists because THM shares `ESegment`,
`EPoint`, `AZURECalc` and the gradient code with the on-shell machinery while
diverging at the observable.
