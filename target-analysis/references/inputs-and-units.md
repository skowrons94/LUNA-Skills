# Inputs and units

## Measurement contract

Identify what Y represents: raw ROI counts, background-subtracted peak area, counts/C, counts/microcoulomb, reactions/incident ion or a relative yield. Record applied dead-time, pileup, branching, angular-distribution, efficiency and charge corrections; do not apply them twice. Clarify whether efficiency is absolute per reaction, per emitted gamma, an addback/ROI acceptance or a differential detector efficiency.

For collected electrical charge Q, positive projectile charge state z and elementary charge e, the incident-ion count is Q/(z e). For a reaction probability y and an effective detection probability eta, counts/microcoulomb = y eta 1e-6/(z e). The example's `y/q_e/1e6*eff` assumes z=1 and a yield per incident ion. Conversely y = (counts/microcoulomb) z e 1e6/eta. If gamma branching is not already included in eta or the cross section, include it explicitly exactly once.

For `Y_error`, establish absolute versus fractional/percent error, standard deviation versus another interval, and correlations. Shared efficiency/charge calibration are correlated nuisance parameters, not independent pointwise noise. Signed background-subtracted yields can be valid; do not discard them automatically. Raw low-count data may need a Poisson likelihood with background rather than Gaussian least squares.

Preserve the actual E column and a converted model-energy column separately. Use acquisition run IDs/times/dose to separate repeated scans or evolving targets. A shared target label is not proof of a single unchanged target state.

## Energy frame

The helper uses **laboratory keV throughout**, including incident energies, energy loss, beam standard deviation, straggling and stopping tables. For a stationary target in the nonrelativistic limit, f=m_target/(m_projectile+m_target), E_cm=f E_lab. Use consistent projectile/target masses and record them.

If a cross-section table is tabulated at E_cm in MeV, relabel its energy grid as E_lab_keV=1000 E_cm_MeV/f while retaining the same total cross-section values. This maps sigma(E_cm(E_lab)); it does not multiply total sigma by an energy Jacobian. Differential angular cross sections need their own frame transformation/acceptance integration.

If integrating in E_cm instead, convert stopping consistently: epsilon_cm=f epsilon_lab(E_cm/f), because dE_cm=f dE_lab. Widths and energy offsets transform too. Using CM energy directly as an argument to a laboratory SRIM table is inconsistent. Do not mix projectile kinetic energy, resonance excitation energy and reaction Q values.

The Boltzmann constant is approximately 8.617333262e-8 keV/K (8.617333262e-5 eV/K). The example labels the latter value as keV/K and uses an energy written as 0.250 alongside keV scan variables. Re-derive the desired thermal broadening in a single unit/frame convention and define whether a formula yields sigma or FWHM; do not repair a mixed-unit expression by changing one constant blindly. The helper accepts a supplied Doppler sigma and does not infer it from that expression.

## Stopping data

The supplied SRIM tables have `Stopping Units = eV / (1E15 atoms/cm2)` and separate electronic/nuclear columns. A table value S corresponds to S*1e-18 keV cm²/atom. The helper parses energy units into lab keV and requires the supported stopping-unit header. Check the table's projectile, elemental/compound identity, version and corrections from its header; the parser does not establish these scientific inputs.

For active species A in a mixture, the Bragg-additive effective stopping per active atom is

epsilon_eff(E)=epsilon_A(E)+sum_i [n_i/n_A] epsilon_i(E).

Examples: CaF2 gives epsilon_F+0.5 epsilon_Ca per F atom; Fe/F and Ta/F ratios are properties to establish, not fixed stoichiometries for every implant. If only one isotope is reactive, distinguish that isotope's abundance from total elemental abundance. For natural/compound tabulations, verify the atom or formula-unit normalization before converting to per-reactive-isotope stopping. Bragg additivity/chemical corrections and stopping uncertainty are model assumptions.

Choose total or electronic stopping based on the modeled energy-loss process. The old notebooks interpolate electronic stopping only; the new parser requires that choice explicitly. Projected-range straggling in angstroms is **not** directly an energy standard deviation in keV; a transport model or justified conversion is required.

## Cross-section input

Record channel and observable (total, differential, S factor or another quantity), units, energy frame, resonance parameters and source. Headerless `.extrap` files need a verified producer/segment definition. Do not assume all files or AZURE output modes share a column layout. Convert barns to cm² with 1e-24 and millibarns with 1e-27. The example sometimes multiplies by 1e3 for plotting; that is not a global cross-section-unit rule.

Resolve narrow resonances finely enough for the integration and fit. Both low-energy target traversal and broadening tails can extend beyond measured scan points. Obtain wider input coverage or justify a physical boundary rule; the helper refuses out-of-range evaluation. Silently extending a table with endpoint values can manufacture long target tails.
