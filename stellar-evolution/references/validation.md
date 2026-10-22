# Validation ladder for stellar-model results

| Rung | Check | Proves | Does not prove |
|---|---|---|---|
| 0 | Installation: a test-suite case reproduces its documented end state (`check-run` ok, values in its README) | the build works | anything about your case |
| 1 | Run health: physical termination code, small cumulative energy error, few retries | the run reached its goal | resolution independence |
| 2 | Resolution: rerun with `mesh_delta_coeff` and `time_delta_coeff` halved (or the case's `varcontrol_target` tightened); the observables change much less than the effect under study | the rate effect is not numerical | physics choices |
| 3 | Known response: the rate change reproduces a published derivative or trend (solar fluxes vs S₁₁₄; C/O after He burning vs ¹²C(α,γ); ²⁶Al vs ²⁵Mg(p,γ) in a published grid) | the pipeline transmits rate changes correctly | that the published model is right |
| 4 | Physics degeneracy: vary the dominant non-nuclear uncertainty of the phase (overshoot f_ov, mixing length, thermohaline efficiency, mass loss) by its plausible range; compare its effect with the rate effect | whether the rate is the limiting uncertainty | — |
| 5 | Post-processing consistency (when a network ran on a model trajectory): the network's energy generation and central abundances track the model's | the handoff is consistent | mixing effects on the network side |

Rungs 0–2 are always required. Rung 3 is required before a new sensitivity is reported. Rung 4 is required before claiming that a measurement would improve a stellar prediction. It is the rung most often skipped, and a referee will ask for it.

Give `physics-referee` the specs, `manifest.json`, the history/profile files and the claim; it recomputes the comparison numbers.
