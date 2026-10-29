# Prompt or delayed, and what a count is normalised to

These notes come from the search for 19F(p,alpha_pi)16O at LUNA 400 kV (4pi BGO, 2024-2026), where a weak signal (511-511 keV
pairs in opposite crystals) had to be separated from photon conversion, room background and beta+ activity made by the
beam. Each section describes a trap that cost a night of analysis, the measured case, why the rule holds and what to do
instead. They apply to any in-beam yield that is small compared with what the beam also produces.

## Normalise a count to the charge of the part of the run that was read

The event-building script read at most 3e7 hits per run to stay fast, and the counts were then divided by the charge of
the whole run. For the ten longest runs only 18-65 % of the data had been read, so their yields came out low by the same
factor: two alpha_pi points at 0.7 MeV b sat among the others at 3.4-3.8 MeV b, and the outlier looked like physics
until the run lengths were compared. The rule is simple: the charge in the denominator must belong to the same events
as the numerator. A cheap way to enforce it is to compare the counts of a reference window with an independent table
of the same run (here the alpha-gamma ROI counts of the collaborator's yield table, which agree to 0.1 % for every run
read completely) and to scale the charge by that coverage, or, better, to read every run completely in chunks; the full
reader processed 2e6 hits per second, so the cap was not needed at all.

## Measure the room background inside the runs, not in a dedicated beam-off run

The dedicated beam-off runs of two beamtimes had four to five times the room rate of the beam-off periods inside the
physics runs (2.0-2.6 MeV: 6.4-7.6 per second against 1.5 per second), evidently because they were taken in another
configuration of the setup. Used as the room template, they made every room-sensitive quantity wrong: the band ratios
used to subtract the room part of the 1.5-3 and 3-5 MeV conversion bands were off by factors of 1.5 and 18, and the
template fit had to scale the room component by 0.3. Periods without beam inside physics runs (a beam trip, the ion
source switched off at night, the DAQ left running after the beam stopped) give the room spectrum in the right
configuration; four such periods in four beamtimes agreed within 10 %. Look for them with the target current of the
current files, then keep a ten-second time series of every observable so that they can be cut out later.

## A weak line under room lines absorbs the mismatch of the room template

The 12C(p,gamma)13N direct-capture line (2.0-2.3 MeV) is the obvious way to measure the carbon on a target, because every
capture makes one 13N and so fixes its activity. In a full-spectrum template fit the 12C template sits under the
214Bi 2204 keV and 208Tl 2614 keV room lines. With a room template of the wrong shape (previous section) the fit put
the residual into the carbon line: for one run at 100 keV it predicted 1920 activity pairs where only 243 pairs were
recorded in total, and for the long runs at 200-220 keV it predicted 6-23 % activity that the time series does not
show. A template amplitude of a weak line in a region dominated by another component must be validated by something
independent of the spectrum shape before it is used. Here the time structure did that, and the carbon amount was
taken from it instead.

## Separate prompt from delayed with the time structure, target by target

A positron emitter made by the beam and a prompt pair source give the same spectrum (both annihilate at the target),
so only time separates them. Four measurements turned out to be robust, in order of strength. First, the decay after
the beam stops: in a run where the DAQ kept recording for 57 minutes after the beam, 30 +- 7 pairs above room were
counted, which is 3.8 +- 0.9 % of the on-beam pair rate as saturated 13N activity, and the first minute after the stop
held 3 pairs against 56 on beam, which bounds a 93 s 17F component at 7 %. Second, the start of a run after at least
ten minutes without beam on the target: the pair-to-ROI ratio in the first minute equals the ratio after ten minutes
(1.008 +- 0.022 stacked over ten runs) when there is no activity, and a fresh 17F, 15O or 13N component would make it
lower. Third, the carry-over at the start of a low-energy run that follows high-energy runs on the same target: the
pairs decayed with tau = 717(71) s (13N; one 862.6 s exponential fits, 11C does not), from which the activity share at
the end of the previous scan was 7-8 %. Fourth, a target whose low-energy runs build up visibly: on one Ta target the
pair rate grew from 12 to 22 per ten minutes in the first hour, which marks the target as carbon-loaded, and its runs
were removed and reported. Carry-over estimates are upper limits, because beam on the target during tuning between runs
does not appear in the current files.

A joint fit of all runs of a target with one contaminant amount and the activity shape computed from the beam history
looks attractive but failed for the short-lived component: in steady state a 93 s activity is proportional to the
current, as the prompt signal is, and the fit traded half of the prompt pairs for 17F against the direct beam-off
measurement. Keep such a fit for long-lived components and check every component it returns against the direct
measurements above.

## Use resonances where the signal is forbidden as a measured baseline

A 0+ alpha particle and a 0+ residual state can only be formed from natural-parity compound states, so the 1+ (340 keV)
and 2- (224 keV) resonances of 19F+p cannot decay by alpha_pi at all. On these resonances the pair-to-alpha-gamma ratio is
pure photon conversion: 8.7e-3 on Ta (simulated 8.5e-3) and 4.8e-3 on Fe (simulated 5.4e-3), while away from them the
ratio rises to 0.03-0.36. A selection rule that switches the signal off at a known energy gives a baseline measured with
the same detector, target and analysis, which tests the simulation and makes the excess model-independent. Look for
such a switch (parity, isospin, a closed channel below its threshold) before relying on a simulated background.

## Measure random pile-up with an offset coincidence window

At a strong resonance the background under a weak high-energy line is two alpha-gammas in one event window. Pairs of
consecutive events whose first hits are 30-330 ticks apart, combined crystal by crystal and weighted by the ratio of
the window widths, give the shape of that pile-up and its expected size from the data, with no model of the source. At
the 340 keV resonance this template reproduced the 12.26 MeV (6.13 + 6.13 MeV) sum peak at a scale of 1.1-1.6. It also
showed that the (p,gamma) sum peak at 13.17 MeV lies under the 6.13 + 7.12 MeV pile-up peak at 13.25 MeV, so the BGO
cannot give the (p,gamma) branchings there; the HPGe, with the primary line at 11.54 MeV resolved, can.
