# Cross-section enhancement, bias and weighted observables

## Decide what the run estimates

Separate three operations:

| Operation | Meaning of an event | Required normalization |
|---|---|---|
| Physical beam transport | One incident projectile, including misses and non-reactions | Generated incident-projectile count plus beam exposure |
| Transport with biased interaction probability | A sampled history under an altered transport law | Correct history/track weights and independent primary count |
| Prescribed reaction products | One sampled reaction or selected channel | Physical reaction probability/channel population supplied separately |

For detector efficiency, prescribed products can be much simpler than enhancing a tiny capture probability, provided depth, energy, angular correlations and cascades represent the desired reaction population. For beam-normalized yield, a per-reaction detector simulation still needs a validated physical yield calculation.

## Where to change the local implementation

The inspected `ParticleCaptureXS`/`ParticleResonantCaptureXS` read numerical vectors and return their values, including their documented isotope fallback. No explicit likelihood-weight correction was found in those inspected cross-section classes or the local output path. Increasing those values must therefore be treated as changing the physical interaction probability until a weight implementation is demonstrated. There is no verified universal “bias factor” macro.

If implementing a configurable factor, keep an immutable physical table and apply the named factor at a single audited point in the cross-section path; record both physical and biased values at representative energies. Trace applicability, isotope selection, process competition and mean-free-path use. Do not also multiply an already enhanced input file. Prefer recording bias configuration in ROOT/run metadata rather than encoding it only in a filename.

A weighted implementation needs a reviewed transport-biasing operator or equivalent derived algorithm, process registration, and scoring changes. Geant4 provides generic biasing machinery, including occurrence and final-state operations. Its interaction and non-interaction corrections are both relevant; a model that merely multiplies sigma does not gain them automatically. Check installed-version support for the selected process, especially a slowing charged projectile, rather than copying a neutral-particle example. See the official [biasing guide](https://geant4.web.cern.ch/documentation/dev/bfad_html/ForApplicationDevelopers/Fundamentals/biasing.html) and [occurrence formalism](https://geant4.web.cern.ch/documentation/pipelines/master/bftd_html/ForToolkitDeveloper/GuideToExtendFunctionality/EventBiasing/eventBiasing.html).

## An analytic check an agent can run

For one absorbing channel in a homogeneous constant-energy slab, let tau=n*sigma*L and b>0 multiply sigma. Then physical probability is `P=1-exp(-tau)` and biased probability is `Pb=1-exp(-b*tau)`. `Pb/b` agrees with P only in the sufficiently thin limit for the chosen b. Even an originally thin target can become optically thick after enhancement.

The likelihood ratio for a reaction at depth x is `w(x)=exp((b-1)*n*sigma*x)/b`; for survival through the slab it is `exp((b-1)*tau)`. These expressions follow from the ratio of exponential flight distributions. The aggregate ratio P/Pb corrects total reaction frequency in this ideal example, but does not restore a biased depth-dependent detector response. With energy loss or competing channels, derive the probability of the entire sampled history rather than reusing this slab expression.

```
python SKILL_DIR/scripts/physics_checks.py slab --optical-depth 0.001 --bias-factor 1000 --interaction-depth-fraction 0.5
```

This reports about 36.8% underestimation from naive division by 1000. It is an analytic teaching/checking tool, not an event-weight repair for existing ROOT files. A file missing the necessary transport history generally cannot be retrospectively corrected by guessing weights.

## ROOT and scoring contract

Before accepting weighted results, add and test the necessary fields described in [root-output.md](root-output.md): primary/history ID, source-normalization convention, process/channel identity, physical/bias settings, selected scoring weight and reaction truth. Distinguish a track's evolving weight from a single valid event weight. Never multiply deposited energy by the weight and then put that changed energy on a spectrum axis; energy is the observable, weight multiplies the tally.

For independent primary histories with scalar scores Xi (zero for failures), an absolute expectation estimator is mean(Xi). Its sample standard error is sqrt(sum((Xi-mean)^2)/(N*(N-1))). Aggregate split descendants into their originating history before calculating uncertainty. `sum(w²)` is useful histogram bookkeeping, but independent-entry errors fail when descendants are correlated. `Neff=(sum w)^2/sum(w²)` is a diagnostic, not a universal confidence interval. A self-normalized ratio `sum(w*f)/sum(w)` answers a different question from a fixed-N absolute yield.

Coincidence gates, addback, multiplicity and thresholds are nonlinear event observables. Independently split/weighted tracks cannot automatically be recombined into a physical coincidence event. Validate the estimator for the actual gate; source-level importance sampling with complete correlated events may be easier to justify.

## Bias scan acceptance

Run b=1 where feasible and at least two modest factors before a large enhancement. Compare corrected yields, reaction-depth and reaction-energy distributions, channel fractions and relevant spectra. Include empty histories, weight extrema and per-history variance. Use independent batches for errors; same-seed runs are a diagnostic, not proof of statistical agreement. Stop increasing bias when variance or depth/competition distortions undermine the estimator. Keep physics-table repairs separate from intentional bias changes.
