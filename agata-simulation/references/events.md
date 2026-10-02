# Event generation

## External event file (`-Ext`)
```
FORMAT 2 0
#
REACTION 1 1 7 14 0.300        # zBeam aBeam zTarget aTarget Ebeam(MeV) (informative)
#
EMITTED 1 1                    # number of emitted types, list of types (1 = gamma)
#
$
-101 8 15 0.0                  # emitter: id Z A E(MeV) (emitter format 2)
 1 7445.08 -0.2230 0.9743 0.0307 0.128 -0.335 0.0     # type E(keV) ux uy uz sx sy sz(cm), lab frame (emitted format 0)
$
-101 8 15 0.0
 1 762.3 ... 
 1 6785.3 ...
$
```
- `FORMAT emitterType emittedType`. Emitted format 0: lab energies and directions plus source position (cm); format 1: c.m. energies (boosted by the emitter velocity); 2/3 without position; 4 energy only.
- `$` separates events; the first `$` ends the header. All γ of one cascade go in one event; AGATA writes them as one output event.
- Doppler, recoil kicks, lifetimes: compute them in your generator and write lab energies (format 0). This is easier to validate than the internal emitter.
- Example generator: `~/Desktop/LUAGATA/src/physics/o15.py` (`sample_cascade`: c.m. velocity, photon recoil kick, exponential decay times, slowing down in the target) and `scripts/run_agata.py` (writes files, runs, converts, manifest).

## Reaction generator (`-TargetEx`)
Used in `~/Desktop/28Si/scripts/run_agata.py` for 3He(28Si,α)27Si* with `/Agata/generator/emitter/BeamIn/*`, `BeamOut/*`, `adistFile` (c.m. angular distribution), `ProjectileExcitation`, and private PhotonEvaporation data via `G4LEVELGAMMADATA`. Requires the D-006 patches; without them all products are created at rest.

### Pitfalls of `-TargetEx` (all found in 28Si; patches in `environment/agata_local_patches.diff`)
- **Products at rest / segfault**: `Outgoing_Beam::ReactionProduct()` must be virtual, otherwise the TargetEx override is never called.
- **α emitted at a single azimuth**: `CAngDistHandler` returns early before initialising `phi_min`, `phi_dif`, `fixedTheta`. Check the φ distribution of the light product in every new setup.
- **Theta window inverted**: the veto rejected events *inside* the window; also `thetaTLF` was computed before `TLF_momentum` and `PLEx/TLEx` were uninitialised.
- **SAURON segments protrude from their chip** (overlap warning, wrong energies): `GetSegments(t − 2·deadSi − 0.4 µm)`.
- **Inverse kinematics**: the heavy beam is the projectile (BeamIn = 28Si at E(3He)·m28/m3); the light target nucleus (3He) is implanted in the target material; give the c.m. angular distribution with `adistFile` (e.g. TALYS dσ/dΩ) and enable `disableFixDepth` + `enableUniformDistr` to spread the reaction depth.
- **γ branchings**: Geant4 PhotonEvaporation may list 0 % branchings for poorly known levels: provide a private copy via `G4LEVELGAMMADATA` with adopted branchings.
- **Lifetimes come from G4ENSDFSTATE** (mean life in ns), not from PhotonEvaporation: for DSAM τ scans, use a private copy via `G4ENSDFSTATEDATA` and check in the output that the decay positions follow the requested τ.
- **Energy conservation** per event (deposited ≤ beam + Q budget) and the reconstructed E_x centroid at the level energy are the minimum checks of a new generator setup.
- For the Δβ lifetime analysis on the output, use the `delta-beta-dsam` skill.

