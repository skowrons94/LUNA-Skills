# Simple geometry construction

## Solids and placements

- `G4Box(name, hx, hy, hz)` takes **half**-lengths; `G4Tubs(name, rmin, rmax, hz, sphi, dphi)` takes a half-length along z and angles in radians (`0, twopi` for a full cylinder). Halving errors are the most common geometry bug: print the full dimensions back.
- `G4PVPlacement(rot, pos, logical, name, motherLogical, false, copyNo, checkOverlaps)` places a daughter in its mother's frame. Coordinates of a daughter are relative to the mother's centre, not the world.
- The rotation in that constructor rotates the frame (it is the inverse of the object rotation). For an intuitive object rotation use `G4PVPlacement(G4Transform3D(rotation, position), ...)`.
- Repeated detectors: one logical volume placed several times with distinct copy numbers. Read the copy number back in the scoring code with `touchable->GetCopyNumber(depth)` (depth 0 = the volume itself, 1 = its mother; the template's gas is depth 0 inside the tube at depth 1).
- Holes and shells: place a daughter of a different material inside the mother (simplest, fastest), or use `G4SubtractionSolid` when a shell must surround another volume at the same level. Boolean solids are slower to navigate; avoid deep chains.
- Make the world slightly larger than everything, of air or vacuum as the setup requires, and start sources inside a vacuum or air volume rather than on a surface.

## Materials

- NIST: `G4NistManager::Instance()->FindOrBuildMaterial("G4_POLYETHYLENE")`, `G4_WATER`, `G4_AIR`, `G4_Galactic`, `G4_STAINLESS-STEEL`, `G4_Cd`, `G4_Al`, `G4_Pb`, `G4_BGO`, `G4_SODIUM_IODIDE`, `G4_Ge`; elements with `FindOrBuildElement("B")`.
- Polyethylene: (CH₂)ₙ by atom count; set the density from the supplier (typically 0.92–0.97 g/cm³) and vary it as a systematic.
- **Hydrogen for thermal scattering**: the thermal-scattering data are attached by name. Build hydrogen as `new G4Element("TS_H_of_Polyethylene", "H", 1., 1.00794*g/mole)` (or `TS_H_of_Water`) and use it in every hydrogenous material, including borated PE; recent versions also map the NIST materials `G4_POLYETHYLENE` and `G4_WATER`. Confirm with the verbose registration list ([physics-lists.md](physics-lists.md)).
- Borated polyethylene by mass fraction: `AddElement(H, (1-f_B) w_H)`, `AddElement(C, (1-f_B) w_C)`, `AddElement(B, f_B)` with w_H = 2·1.008/14.027 and f_B the boron mass fraction from the datasheet (often quoted as weight-% of B, sometimes of B₂O₃ or B₄C: convert). Natural boron is about 20 % ¹⁰B by atoms; enriched boron needs explicit isotopes.
- Enriched or pure isotopes: `G4Isotope("He3", 2, 3, 3.0160293*g/mole)`, then `G4Element` with `AddIsotope(iso, abundance)`.
- **Gas at pressure** from the ideal gas law, ρ = p M / (R T):

  ```cpp
  const G4double M = 3.0160293*g/mole;                       // 3He
  G4double rho = p * M / (k_Boltzmann * Avogadro * T);      // Geant4 units; R = k_B N_A
  auto gas = new G4Material("He3_gas", rho, 1, kStateGas, T, p);
  ```

  At 4 bar and 293.15 K this gives 4.95 × 10⁻⁴ g/cm³; print the density at construction and compare with the hand value. Give gases and moderators their temperature: the HP models use the material temperature for Doppler broadening and thermal motion.
- Mixtures (detector gas with quench gas, concrete, steel grades): use the composition from the supplier or a cited compilation and record it.

## Overlaps

- Check every placement: `pv->CheckOverlaps(resolution, tolerance, verbose)` returns true on an overlap or protrusion from the mother; count them and abort construction if any (the template does). Alternatively run `/geometry/test/run` after `/run/initialize`.
- An overlap makes the navigation, and hence every result, undefined. "Overlap is detected" in a log is a failure, also when the run completes.
- After changing a parameter (ring radius, tube size, shell thickness), rerun the overlap check: a valid default does not make the scanned range valid.

## Parametrising geometry

- Expose dimensions through `G4GenericMessenger::DeclarePropertyWithUnit("name", "cm", variable)` so that macros set them with units (`/app/geo/ringR 8 cm`), and set them before `/run/initialize`.
- One geometry per process is the simplest reliable pattern: a scan is a list of macros or command-line values, each in its own run directory. Changing geometry after initialisation requires `/run/reinitializeGeometry` and a `Construct()` that cleans the old stores; test this before relying on it.
- Command-line options for a few global switches (physics list, thermal scattering on or off, seeds) are clearer than macro commands, and are printed and stored with the outputs.
- Use Geant4 units everywhere inside the code (`x*cm`, `E*MeV`); divide by the unit when printing or writing (`x/cm`) and put the unit in the output key (`ring_r_cm`).
- Write the full geometry configuration into each output file; a result without its geometry is not reusable.
