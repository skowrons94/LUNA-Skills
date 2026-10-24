# Writing style for LUNA-Skills

A skill tells an agent, and a student reading along, how to do one research task. It should read like an experimentalist explaining the method to a new student: what the task is for, what is done in which order, why each rule exists, and what goes wrong. This guide derives that register from the owner's papers and from three methods papers, and is consistent with `clear-experimental-writing` (manuscript-guide.md §§13, 14, 17) and `methods-paper-style` (§§1, 4, 6).

Corpus (Zotero keys): owner's papers M5C2PPCD (PRC 107 L062801, 2023), UGMDN7BB (PRL 131 162701, 2023), YML3ITJT (PRC 111 064611, 2025), WJ77Z7T3 (PRC 111 035802, 2025), 3UTZAF4A (J. Phys. G, 2023, BGO); methods papers BHW47FJJ (Azuma 2010, AZURE), KLYGYABV (Longland 2010, Monte Carlo rates), RJ5RPPYH (Adelberger 2011, Solar Fusion II). Gap measured on yield-analysis, resonance-search, cluster-potential and stellar-evolution SKILL.md.
Method: `pdftotext` in reading order (no `-layout`), body text up to the references, prose paragraphs only; the measurement scripts (`measure.py`, `extra.py`, `grepsent.py`, `locate.py`) and raw numbers (`metrics.json`) were kept with the review of 2026-10-25, not in this repository. The counts are regex heuristics (sentence splitting, a be + participle test for the passive); treat them as ±20 %. Colon and semicolon counts of UGMDN7BB and RJ5RPPYH are inflated by the APS math encoding ("0:144", "(p; γ)") and are left out. Page numbers below are PDF pages.

## 1. Measured features

| Feature | Owner's papers (5) | Methods papers (3) | Current skills (4) |
|---|---|---|---|
| Sentence length, median (words) | 20–24 | 22–23 | 11.5–17 |
| Interquartile range (words) | 12–32 | 14–31 | 7–25 |
| Sentences > 35 words | 12–18 % | 14–18 % | 0–5 % |
| Sentences per paragraph, median | 5–7 | 4–9 | 1–3 |
| Sentences with we/our | 3–5 % (PRC), 10 % (J Phys G), 22 % (PRL) | 4–20 % | 0 % |
| Passive sentences | 38–57 % | 32–49 % | 8–12 % |
| Imperative sentences | 0 % | 0–1 % | 22–64 % |
| Purpose-first sentences ("To ..., ...") | 2–6 % | 1 % | 0 % |
| Sentences with a causal link (because, since, given, thus, so that, to check ...) | 6–16 % | 10–18 % | 0–3 % |
| Sentences with a negation (not, no, never, cannot) | 2–10 % | 6–13 % | 11–25 % |
| Parentheses holding a clause (≥ 12 characters of words), per sentence | 0.01–0.15 | 0.04–0.18 | 0.20–0.37 |
| Colons / semicolons per 1000 words | 1.1–1.7 / 0.3–0.6 | 0.5–1.2 / 1.1–1.7 | 0–22 / 4–20 |
| Bold spans per 1000 words | 0 | 0 | 0–20 |
| must / should / never per paper | ≤ 1 / 0 / ≤ 2 | 5–16 / 9–11 / ≤ 1, each with a condition | resonance-search: 6 / 0 / 8 in 1700 words |
| Uncertainty notation | compact: 2369.6(4) keV (31–67 per PRC), % for relative | ± (Azuma: 83) | almost none |
| Description field (characters) | own writing skill: 354 | – | 237–1049 across the 31 skills, median 614 |

What the numbers say. The owner writes moderate sentences (about 22 words, a quarter above 30), in paragraphs of five to seven sentences, mostly in the passive with "we" for decisions and checks. Almost every procedure arrives with its purpose or its reason. The skills invert this: sentences half as long, one-sentence paragraphs, imperatives, three times more negations, a parenthesis carrying a second clause in every third to fifth sentence, and almost no "because". The reasons exist, usually in the references, but the SKILL.md states rules without them.

### Evidence (short quotes)

Purpose before procedure:
- "To keep the dead time below 2%, the detector A was moved to 10.0(2) cm distance from target, middle geometry in Fig. 1, when investigating the 551 keV resonance." (YML3ITJT, Sec. II, p. 3)
- "To prevent degradation, the target backing was in direct contact with water at a set temperature of 16 °C." (YML3ITJT, Sec. II, p. 3)
- "To fix this issue, the limfit package [33] was used instead of minuit2." (WJ77Z7T3, Sec. II C, p. 5)

Caveats with a size and a reason:
- "For the summing correction a conservative uncertainty of 50% was assumed, given the small impact on the efficiency results." (M5C2PPCD, Experimental setup, p. 3)
- "Summing effects were negligible for detectors B and C because of their large distance from the target ..." (YML3ITJT, Sec. III, p. 4)
- "For the studies that do not report any systematic uncertainty, a value of 20% was considered." (M5C2PPCD, Results, p. 4)
- "The best-fit parameter errors for the frequentist approach indirectly depends on the assumption that the reduced chi-squared, χ²dof, is close to 1." (WJ77Z7T3, Sec. II C, p. 4)

Exclusions and limits stated as facts, not prohibitions:
- "Detector C was removed for technical reasons and replaced in a different position before runs at Ep = 400 and 465 keV without reperforming a proper efficiency calibration, thus these data are not included." (M5C2PPCD, Data analysis, p. 4)
- "With the modest energy resolution of the BGO detector, the signature of a single γ-ray produced by the 2H(p,γ)3He reaction (Q = 5493 keV) cannot be resolved from the signal of 17O(p,γ)18F (Q = 5607 keV)." (3UTZAF4A, Sec. 3, p. 13)
- "The origin of such discrepancies is unclear, but may arise from an inaccurate treatment of target thickness effects in the literature ..." (UGMDN7BB, p. 4)

Observation first, checks with "we":
- "Over the whole energy range, a 20% scaling difference is observed between present results and literature data for the main transition [11,26,27]." (YML3ITJT, Sec. IV, p. 5)
- "Further, we compared yields obtained from HPGe measurements on evaporated targets with additional runs on natC targets, finding an overall agreement within 2%." (UGMDN7BB, p. 3)

How methods papers give instructions (condition, then requirement):
- "As a rule of thumb, if the resonance energy falls outside the range [of the Gamow peak] then, even for a narrow resonance, the rate contribution from the resonance wing must be taken into account." (KLYGYABV, Sec. 2.3, p. 5)
- "For use in stellar model calculations, the results presented here must be corrected, if appropriate, for (i) electron screening at elevated densities, and (ii) thermal excitations of the target nucleus at elevated temperatures." (KLYGYABV, Sec. 1, p. 3)
- "We adopt this fitting procedure, despite our earlier arguments favoring fitting formulas that are motivated by theory, because the energy window of interest is fully covered by the experiments." (RJ5RPPYH, Sec. IV, p. 17)
- "... our Eqs. (21) and (23) follow the sign convention of Refs. [21,25] and consequently differ from those of Ref. [14] by an overall minus sign (which has no effect upon observables)." (BHW47FJJ, p. 4)

Other habits. Cross-references are short and specific: "see Table I and Fig. 1 for details", "Eq. (3)", "Ref. [11]", "see Supplemental Material [38]"; "above/below" is rare (0–6 per owner paper). Transitions are few and logical, about one per 200 words: however, thus, moreover, in addition, on the other hand, indeed, finally, hence. Hedges are numbers or "about", "within", "consistent with", "conservative(ly)". Ranges use an en dash with the frame in the symbol: "E = 320–620 keV", "Ep = 350 and 670 keV". The owner does use "crucial" (4 times in YML3ITJT and in 3UTZAF4A) and "comprehensive" (4 in M5C2PPCD), so there is no word blacklist; what is absent is the instruction register: no "never", no "non-negotiable", no bold, no colon chains.

## 2. Rules for skill prose

1. Sentences. Aim at a median of 18–22 words; most between 12 and 30. Split anything above about 35 words. Do not string fragments of under eight words; join a rule and its reason into one sentence ("..., because ...").
2. Paragraphs. An explanatory paragraph has three to six sentences: the statement, the reason or mechanism, the consequence or check. One idea per paragraph (manuscript-guide §3).
3. Voice. Explanations in the present tense, declarative, passive where the procedure matters more than the actor, "we" for the lab's choices and conventions ("We bound the poles formally ..."). Imperatives belong in numbered steps and next to commands. Target: under a third of sentences imperative, concentrated in the steps.
4. Every rule carries its reason. State the rule, then why, then how to check it. Take the reason from the skill's references, from a validation record or from the owner; if no reason is known, leave the rule as it is and add it to the list of open reasons in the commit or review note for the owner; never invent one. A requirement uses "must" with its condition (methods-paper pattern: "if X, then Y must ..."). Keep "never" and "always" for data integrity (published data are not edited, the installation is not edited).
5. Caveats and pitfalls as observations: what happens, under which condition, how large, what to do. "A finite Coulomb radius changes the phase by 0.008 rad at 1 MeV" beats "Beware Coulomb radius". Give the case and the number when the skill learned it from a run (the 7Be scattering length, the 9 GB AGB run).
6. Numbers. Value, uncertainty, unit, frame and origin: "10.0(2) cm", "3.5 %", "E = 320–620 keV (c.m.)"; thresholds say where they were measured ("measured 2026-10-23, memlog.tsv"). A number without its source is a guess to the reader.
7. Parentheses hold a symbol, a value, a unit, a citation, a file or a command, never a second clause. If the parenthesis contains a verb, make it a sentence. One parenthesis per sentence is plenty.
8. Colons introduce a list, an equation or a command, not a chain of clauses. Semicolons rarely; two sentences are clearer (methods-paper-style §6).
9. No bold or italics in running text. Structure comes from headings and topic sentences. A bold label in front of a bullet becomes either a heading or the first sentence of the paragraph.
10. Lists are right for: steps executed in order; commands; deliverables (files to produce); a routing table (task → skill); parameters with values; checklists. Lists are wrong for: rules with reasons, physics explanations, caveats whose items depend on each other, anything that needs "because" or "therefore" between items. A list item is one parallel sentence; if it needs three, it is a paragraph.
11. Transitions carry logic, about one per paragraph: therefore, because, so that, for this reason, however, in contrast. None of "It is worth noting", "Importantly", "Crucially" (manuscript-guide §14).
12. Cross-references: name the file and what it holds, once, at the point of need: "Node counting and the width conventions are explained in [physics.md](references/physics.md)." No "(see below)"; state the thing where it is used.
13. Headings are plain nouns of the content: "What the method assumes", "Rules and their reasons", "Pitfalls", "What to deliver". Not "Non-negotiable boundaries", "Pitfalls that cost days", "Route the task".
14. Length. SKILL.md: the method and the rules, up to about 150 lines; detail, derivations and long pitfall histories in references/*.md, which follow the same prose rules.

## 3. Skill template

```markdown
---
name: skill-name
description: <Verb> <object> with <method or tool>, <two or three main sub-tasks>. Use when <trigger
  phrased as the user would say it>, <second trigger>, or <third>; <one boundary sentence, e.g.
  "use `azure2` for single fits" or "these numbers must be computed, not recalled">.
---
# Title (the task, in plain words)

<Opening paragraph, 3–5 sentences. The question the skill answers and why it matters physically;
what you need (inputs, files, software); what you get (outputs, with their form).>

## Where this fits
- Comes from: <upstream skill or data, with the contract or file name>
- Goes to: <downstream skill, contract>
- Checked by: <subagent, selftest, validation rung>

## Method
<One paragraph on the idea of the method, then numbered steps. Each step: the action (imperative
allowed), its purpose in the same sentence or the next, the command or file.>
1. ...
2. ...

## Rules and their reasons
<Numbered short paragraphs, 2–4 sentences each, plain first sentence (no bold): the rule; the reason;
how to check it. Numbered so other text can say "rule 3".>

## Pitfalls
<Short paragraphs or one-sentence items: condition, what happens, size, remedy, where it was seen.>

## Scripts
<code block of commands with one-line comments; "Replace SKILL_DIR with this skill's directory.">

## What to deliver
<List of files and numbers, the contract they satisfy, where they are written.>
```

Description field. The agent chooses a skill from this field alone, so it must contain the words a user or another skill will use: tool names (MESA, AZURE2, .azr, pynucastro, KSHELL, Geant4, ROOT), observables and nuclei (12C/13C, ANC, θ², 26Al), and verbatim phrases users say ("automatic resonance fits"). Pattern: what the skill does in one sentence, "Use when ..." with two to four triggers, one boundary clause. Target 300–500 characters; up to about 600 for broad skills. Move enumerations of sub-topics into the opening paragraph or the reference list, but keep each distinctive trigger noun. Keep "must be computed, not estimated from memory" (or a shorter "must be computed, not recalled") where it exists: it makes the agent use the skill instead of answering.

Example, stellar-evolution, 1003 → 610 characters, triggers kept (MESA, SDK, admin rights, solar, AGB, 13C pocket, massive stars, pair instability, AZURE2, 26Al, neutrino fluxes, trajectories, one-zone networks, core masses, surface or wind abundances, burning conditions, installed, run, debugged); "carbon ignition", "history and profile output" and the "resolution and physics-degeneracy checks" move to the body:

> Set up, run and check MESA stellar-evolution models for nuclear-astrophysics questions: installing MESA and its SDK without admin rights, test-suite templates (solar, AGB and 13C pocket, massive stars, pair instability), changed or tabulated rates (e.g. from AZURE2, 26Al isomers), and solar neutrino fluxes or trajectories for one-zone networks. Use when a rate's effect on a star is needed (structure, lifetimes, core masses, surface or wind abundances), when the burning conditions of a star or phase are asked for (these come from a model, not from memory), or when MESA must be installed, run or debugged.

## 4. Before and after

Facts, numbers, file names and commands are kept; reasons added in the rewrites come from the skill's own references (cited) or follow from the original sentence.

### A. cluster-potential, "Non-negotiable boundaries" 1–3

Before:
> 1. **The potential binds exactly the forbidden states.** Count them with `n_forbidden` (Wildermuth: N = 2n + l < N_min) and check every fitted depth with `pauli_ok`. A shallow potential with the right level energy and the wrong node count is a different model.
> 2. **Fix the range once, on one band; fit depths per partial wave on known levels.** Every other number is then a prediction. Say which numbers were fitted and which were predicted.
> 3. **A local potential has no exchange.** It cannot produce the parity dependence that antisymmetrization gives (mu_N differs between odd and even N). A positive-parity prediction from depths fitted to negative parity is a test of locality, not of the data. The 7Be case gave a scattering length of the wrong sign (-31 fm against +22 to +60 fm measured).

After (heading "What the model assumes"):
> 1. A deep potential respects the Pauli principle only if it binds exactly the forbidden states, which in Wildermuth's counting are those with N = 2n + l < N_min. Count them with `n_forbidden` and check every fitted depth with `pauli_ok`. A shallow potential that gives the right level energy with the wrong number of nodes is not a cheaper version of the same model but a different model.
> 2. The Gaussian range is fixed once, on one band, and one depth per partial wave is then fitted on a known level. Every other number the model gives is a prediction, and only the predictions test the model. The results must therefore say which numbers were fitted and which were predicted.
> 3. A local potential contains no exchange, so it cannot produce the parity dependence that antisymmetrization introduces; the norm-kernel eigenvalues mu_N show it, since they differ between odd and even N. When depths fitted to negative-parity levels predict a positive-parity quantity, the comparison tests the locality assumption, not the data. In 7Be this test fails: the predicted scattering length has the wrong sign, -31 fm against +22 to +60 fm measured.

### B. stellar-evolution, opening and boundaries 3, 4, 6

Before:
> A rate change matters to astronomy through a star: its structure, timescales, mixing and what it ejects or emits. Run that star from a maintained template with one named change, check that the run reached its goal and that the effect is larger than the numerical and physics noise of the phase, and keep every run reproducible from a spec.
> 3. **A changed rate gets a run-local cache** (`rates_cache_dir = './rates_cache'`) and a net in which the reaction is explicit. A factor on a reaction the net lacks does nothing. Confirm it in the run's reaction list.
> 4. **Tabulated rates are resampled densely** (`mesa.py rate-table`). MESA interpolates tables linearly in rate vs T8. Rates are bare (MESA screens).
> 6. **Judge a run by its termination code and energy error** (`mesa.py check-run`), not by the existence of output. A solver-limit termination is a failed run.

After:
> A reaction rate reaches an astronomical observable only through a star, that is, through its structure and timescales, its mixing, and what it ejects or emits. This skill measures that effect in a MESA model. You need the observable (core mass, lifetime, surface ratio, yield, neutrino flux), the star or phase, and an idea of the precision that would matter. You get runs from a maintained template that differ by one named change, a check that each run reached its goal, and a comparison of the effect with the numerical and physics noise of the phase. Every run is reproducible from its spec.
>
> 3. A changed rate needs a run-local rate cache, set with `rates_cache_dir = './rates_cache'`, because the shared cache does not know that the rate changed (nuclear.md). The reaction must also be explicit in the net: a rate factor on a reaction the net lacks does nothing. Confirm the reaction in the run's reaction list.
> 4. MESA interpolates rate tables linearly in rate against T8. Tabulated rates are therefore resampled densely with `mesa.py rate-table`, onto 2000 log-spaced points (nuclear.md). The tables contain bare rates, because MESA applies the screening itself.
> 6. A run is judged by its termination code and its energy error, both reported by `mesa.py check-run`, not by the existence of output. A run that stopped at a solver limit has failed, even if it wrote histories and profiles, because it did not reach the physical stopping condition of its case (running.md).

### C. resonance-search, "Physics limits" and "Normalisations"

Before:
> - **Physics limits.** θ² ≤ 1 in every channel for levels inside the data range. Background poles above it may exceed 1 up to a stated cap. Say which form the bound uses:
>   - formal: γ²/(ħ²/μa²), the natural fit bound;
>   - observed: Γ_c/Γ_W, with Γ_W = 2P_l(E_r)ħ²/(μa²).
>
>   The two forms differ by the level-shift factor, which is 70+ for distant poles. Bound the poles formally and audit them on the observed θ².
> - **Normalisations** float only with a prior equal to the stated systematic uncertainty, and are written to the segment line (they do not survive a generic write-back). When you fit through the pyazr residual API, add the prior term ((n−1)/σ_sys)² explicitly. Arbitrary-scale data (THM, unpublished yields) get an unconstrained or profiled norm and are plotted scaled.

After:
> Levels inside the data range must have θ² ≤ 1 in every channel. Background poles above the data range may exceed 1, up to a cap that is stated with the result. The reduced width can be expressed in two forms, and the report says which one a bound uses. The formal form, γ²/(ħ²/μa²), is the natural bound for the fit. The observed form is Γ_c/Γ_W, with Γ_W = 2P_l(E_r)ħ²/(μa²). The two differ by the level-shift factor, which exceeds 70 for distant poles, so a pole within the bound in one form can be far outside it in the other. We therefore bound the poles in the formal form and audit them on the observed θ².
>
> The normalisation of a data set may float only with a prior whose width equals the stated systematic uncertainty of that data set. Write the fitted normalisation to the segment line, because a generic write-back does not keep it. A fit through the pyazr residual API does not include the prior, so add the term ((n−1)/σ_sys)² explicitly. Data on an arbitrary scale (THM, unpublished yields) get an unconstrained or profiled normalisation and are plotted scaled.

## 5. What not to change

- Technical terms and symbols: θ², γ², Γ_W, ANC, mu_N, N_min, Brune parametrisation, formal/observed, bare rates, c.m./LAB frames, C_t, T8. Do not replace a term with a synonym (manuscript-guide §15).
- Commands, options, function and file names, paths and inlist keys, exactly as written (`mesa.py check-run`, `rates_cache_dir = './rates_cache'`, `pauli_ok`, `SKILL_DIR`, `results.json`).
- Every number, with its unit, uncertainty, frame and date of measurement; every range and threshold (70+, 0.008 rad, 2000 points, 4–6 GB).
- Citations, Zotero keys and references to project files (VALIDATION.md, memlog.tsv).
- Trigger words and verbatim user phrases in the description, and the "must be computed, not estimated from memory" clause.
- Contract names (`yield-table`, `rate-table`), skill names in routing, and selftest expectations ("must print PASS").
- Code blocks: keep them as they are; only their one-line comments may be rewritten.
- The substance of every rule and pitfall. A rewrite may add a reason from the references, never remove a rule or soften a requirement.
