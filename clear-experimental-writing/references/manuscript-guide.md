# Clear Experimental Writing

## Purpose

Use this skill to make an experimental nuclear-astrophysics paper easy to follow on the first reading.

The central principle is:

**Every paragraph should answer one question that the reader naturally has at that point in the paper.**

The preferred logical sequence is:

**astrophysical problem → nuclear-physics uncertainty → experimental gap → measurement strategy → experimental implementation → extraction of the observable → uncertainty → comparison → physical consequence**

Do not expose technical details before the reader knows why they matter.

---

# 1. Overall style

Write in restrained, precise scientific English.

Prefer:

- concrete statements over rhetorical emphasis;
- physical quantities over qualitative adjectives;
- short logical transitions over elaborate signposting;
- one main idea per paragraph;
- chronological or causal order within experimental descriptions;
- explicit comparisons with previous work;
- cautious interpretation supported directly by the data.

The prose should feel authoritative because the reasoning is transparent, not because strong adjectives are used.

Avoid promotional words such as:

- groundbreaking
- unprecedented
- revolutionary
- extremely important
- crucially important
- remarkable

unless the statement is quantitatively justified.

Prefer statements such as:

> The new measurement reduces the uncertainty from X to Y.

rather than:

> The new measurement represents a major improvement.

---

# 2. The information funnel

## Introduction

Build the introduction from broad to narrow.

### Paragraph 1 — astrophysical context

State:

1. what astrophysical process or environment is involved;
2. what the reaction controls or influences;
3. why its rate matters.

Do not begin with experimental apparatus.

Do not spend several paragraphs reviewing general nuclear astrophysics unless it is necessary for understanding the problem.

### Paragraph 2 — reaction-specific problem

Identify the actual nuclear-physics uncertainty.

Examples:

- unknown resonance strengths;
- conflicting measurements;
- uncertain low-energy extrapolation;
- poorly constrained branching ratios;
- disagreement between direct and indirect measurements.

Whenever possible quantify the uncertainty.

Instead of:

> The reaction rate is highly uncertain.

prefer:

> At \(T=...\), existing evaluations differ by a factor of ...

or:

> Below \(E=...\), only upper limits are available.

### Paragraph 3 — state of the art

Describe previous experiments selectively.

Do not construct a historical catalogue.

For every previous result mentioned, explain why it matters to the present measurement.

Useful structure:

> Previous measurements determined X. However, Y remains unconstrained because Z.

When experiments disagree, state the disagreement clearly and neutrally.

### Final introduction paragraph — present experiment

End the introduction by answering:

**What exactly does this work do that resolves the problem just described?**

Typical structure:

> To clarify this situation, we performed...

Then state:

- facility;
- observable;
- energy range;
- principal experimental advantage.

Do not reveal all results here unless required by the journal format.

---

# 3. Paragraph architecture

A strong paragraph usually follows:

**topic → evidence/detail → consequence**

Example pattern:

1. State what was done.
2. Give the necessary quantitative information.
3. Explain why it matters.

Avoid paragraphs that mix:

- detector geometry,
- astrophysical interpretation,
- calibration,
- literature review,
- uncertainty estimation

without a clear hierarchy.

If the reader changes conceptual level, consider starting a new paragraph.

---

# 4. Experimental sections

Describe the experiment primarily according to the path followed by the measurement.

A useful order is:

**beam → beam transport → target → detection → acquisition → calibration/efficiency → monitoring**

For each component, immediately state its purpose when that purpose is not obvious.

Prefer:

> A cold trap in front of the target limited the deposition of contaminants, and an electrode at negative potential returned secondary electrons so that the beam current was measured correctly.

rather than describing a component first and explaining its function several paragraphs later.

Similarly:

> A second detector monitored the competing channel, which provided an independent check of the target thickness.

is preferable to giving detector specifications before telling the reader why the detector exists.

## Quantitative details

Keep numbers that affect:

- reproducibility;
- efficiency;
- backgrounds;
- energy definition;
- normalization;
- systematic uncertainties.

Remove specifications that have no later relevance.

The experimental section should not read like an equipment inventory.

---

# 5. Explain design choices

Whenever an unusual choice appears, answer **why**.

Examples:

- Why this detector angle?
- Why this target material?
- Why this beam current?
- Why this reference resonance?
- Why this shielding thickness?
- Why simultaneous detection of another channel?
- Why an underground measurement?

This often requires only one clause.

Good:

> The detector was placed at a backward angle so that the two reaction products are separated in energy.

Less useful:

> The detector was placed at a backward angle.

---

# 6. Analysis sections

Introduce the observable before the algebra.

Preferred order:

1. state what is being extracted;
2. explain the measurement strategy;
3. give the equation;
4. define every term;
5. explain corrections;
6. state uncertainty contributions;
7. present the resulting quantity.

Do not begin a subsection with a long equation unless the physical purpose is already obvious.

When using a relative measurement, explicitly state what cancels and what remains.

When using simulations, state separately:

- what the simulation determines;
- how it was validated;
- how its uncertainty enters the result.

---

# 7. Treatment of uncertainties

Uncertainties should be part of the analysis narrative, not an appendix added after the result.

Distinguish clearly between:

- statistical uncertainty;
- point-to-point systematic uncertainty;
- common normalization uncertainty;
- model-dependent uncertainty.

Whenever possible identify the dominant terms.

Use the structure:

> The uncertainty is dominated by X, while Y and Z contribute ...

or:

> Error bars include X and Y. An additional common normalization uncertainty of Z% is not shown.

Do not repeatedly say that uncertainties were “carefully evaluated.” Show how they were evaluated.

---

# 8. Presenting results

Lead with the observation.

Prefer:

> The results from the individual targets agree within their uncertainties.

then explain how the combined value is obtained.

Avoid beginning with an extended methodological qualification before telling the reader what happened.

Useful sequence:

**observation → consistency checks → quantitative result → comparison with literature → interpretation**

Keep interpretation proportionate to the sensitivity of the experiment.

Use:

- “consistent with”
- “shows no evidence for”
- “rules out within...”
- “supports”
- “disfavours”
- “suggests”

according to what the measurement actually establishes.

Do not turn “we do not observe X” automatically into “X does not exist.”

---

# 9. Figures

Introduce a figure because it answers a question in the text.

Do not merely write:

> Figure 3 shows the results.

Instead:

> The resulting S factors are shown in Fig. 3 together with previous measurements and theoretical calculations.

Then immediately identify the important feature:

> All targets give consistent results and no resonant structure is observed near ...

Do not narrate every graphical element already obvious from the caption.

Captions should be sufficiently self-contained to explain:

- quantity plotted;
- datasets;
- meaning of bands or lines;
- uncertainty represented by error bars.

---

# 10. Comparison with literature

Make comparisons quantitative whenever possible.

Prefer:

> The present value is lower than X by an amount smaller than the combined uncertainty.

instead of:

> Good agreement is found.

When data disagree, avoid implying a cause unless demonstrated.

Use:

> The origin of this discrepancy is unclear.

or:

> The difference can largely be traced to the adopted normalization...

only when evidence supports it.

---

# 11. Discussion

Move from the measured quantity outward.

Preferred sequence:

**experimental result → nuclear interpretation → reaction rate/evaluation → astrophysical implication**

Do not suddenly return to detector details in the astrophysical discussion.

Separate statements that are measured directly from those inferred through a model.

Use wording such as:

> Within the adopted R-matrix description...

when a conclusion depends on model assumptions.

---

# 12. Conclusions

Keep conclusions short.

A strong conclusion normally contains four elements:

1. what was measured;
2. over which range / with what precision;
3. what nuclear-physics question was resolved;
4. what consequence follows.

Example architecture:

> We measured X over Y. The resulting uncertainty is Z. The data show/rule out/constrain A. The corresponding reaction rate therefore B, reducing the uncertainty relevant to C.

Do not repeat the whole introduction.

Do not introduce new methodological details.

Finish on the physics consequence, not on a generic claim of importance.

---

# 13. Sentence style

Prefer sentences of moderate length with one logical backbone.

Use subordinate clauses when they clarify causal relationships, but avoid chains of three or four qualifications.

Prefer:

> The uncertainty is dominated by the detector efficiency, which contributes 6%.

over:

> The uncertainty, which arises from a number of sources associated with the experimental setup and analysis procedure, among which detector efficiency represents the most relevant contribution, amounts to...

Use active and passive voice pragmatically.

Good active forms:

> We measured...
> We adopted...
> We determined...
> We used...

Good passive forms when the procedure is more important than the actor:

> The efficiency was determined using...
> The target thickness was monitored by...

Avoid excessive “we” but do not contort sentences merely to eliminate it.

---

# 14. Transitions

Use transitions to express logic, not decoration.

Useful transitions include:

- However,
- Therefore,
- In contrast,
- In addition,
- As a result,
- To assess...
- To verify...
- To reduce...
- For comparison...
- In order to clarify this situation...

Avoid frequent:

- It is worth noting that...
- Interestingly...
- Remarkably...
- It should be emphasized that...
- Needless to say...

If something is important, state the fact directly.

---

# 15. Terminology

Introduce notation once and use it consistently.

Avoid alternating casually between:

- resonance energy / beam energy / center-of-mass energy;
- yield / counting rate / counts;
- uncertainty / error;
- evaluation / fit;
- detector efficiency / acceptance.

When several energy definitions occur, explicitly establish the convention early.

Use conventional nuclear-astrophysics terminology rather than ornate synonyms.

---

# 16. Equations

An equation should solve a problem introduced in the preceding sentence.

Before an equation, say what quantity is being calculated.

After it:

- define symbols;
- state input quantities;
- identify corrections;
- state where uncertainties enter.

Do not leave equations isolated from the experimental narrative.

---

# 17. Things to remove during revision

Delete or rewrite sentences that:

- repeat information from the previous paragraph;
- announce obvious structure;
- contain two unrelated ideas;
- make qualitative claims that can be quantitative;
- provide apparatus specifications never used again;
- give historical detail unrelated to the present uncertainty;
- overstate agreement or disagreement;
- explain a motivation after the corresponding procedure has already been described.

Particularly question phrases such as:

> It is important to note that...

> It is interesting to observe that...

> As already mentioned before...

> In order to better understand...

Usually the sentence can begin directly with the information that follows.

---

# 18. Preferred manuscript flow for an experimental paper

For a full experimental article, default to:

## 1. Introduction
Astrophysics → reaction → present uncertainty → previous measurements → unresolved question → present work.

## 2. Experimental setup
Facility/beam → target → detectors → current/normalization → calibration → background control.

## 3. Data analysis
Observable → yield extraction → efficiency → corrections → normalization → uncertainty budget.

## 4. Results
Measured quantities → consistency tests → combined values → literature comparison.

## 5. Interpretation / reaction rate
Model or R-matrix analysis → derived quantities → reaction rate → comparison with evaluations.

## 6. Astrophysical implications
Only if substantial enough to justify a separate section.

## 7. Conclusions
Measurement → main numerical result → resolved uncertainty → consequence.

Merge sections when the manuscript is short rather than artificially multiplying headings.

---

# 19. Revision mode

When revising existing text, do not automatically rewrite every sentence.

First diagnose:

### A. Logical placement
Is this information appearing at the point where the reader needs it?

### B. Paragraph purpose
Can the paragraph's purpose be stated in one sentence?

### C. Causal clarity
Does the text explain why the procedure was necessary?

### D. Quantitative precision
Can vague claims be replaced by numbers?

### E. Redundancy
Has the same physical motivation already been stated?

### F. Result-first presentation
Does the reader learn the principal observation before secondary qualifications?

### G. Scope discipline
Does the text distinguish what was measured from what was inferred?

Make the **minimum changes required** to fix these issues unless the user requests a complete rewrite.

Preserve technically precise wording supplied by domain experts.

---

# 20. Special mode: editing the user's manuscripts

For technically mature drafts:

- preserve the physics content unless an inconsistency is detected;
- prefer restructuring and sentence-level simplification over wholesale rewriting;
- retain quantitative detail;
- do not remove caveats required for scientific accuracy;
- look especially for paragraphs in which the motivation arrives after the technical detail;
- bring the physical purpose of each measurement or correction forward;
- prevent R-matrix/model discussion from obscuring the experimental result;
- make uncertainty treatment explicit but compact.

The target is not popular-science prose.

Assume a nuclear-physics reader, while making the logical structure sufficiently transparent that a non-specialist nuclear physicist can still follow the argument.

---

# 21. Final checklist

Before returning a revision, verify:

- [ ] Does the introduction end with the precise unresolved question and the present measurement?
- [ ] Does each paragraph have one dominant purpose?
- [ ] Is every important experimental component connected to its function?
- [ ] Are energy definitions unambiguous?
- [ ] Are measured and model-derived quantities clearly distinguished?
- [ ] Are uncertainty sources stated where the result is derived?
- [ ] Are literature comparisons quantitative?
- [ ] Are conclusions proportional to the experimental sensitivity?
- [ ] Is unnecessary historical material removed?
- [ ] Is repetition minimized?
- [ ] Does every figure discussion identify the physical message?
- [ ] Does the conclusion end with the consequence of the measurement?
- [ ] Could a nuclear physicist outside the immediate subfield understand why each section follows the previous one?

# Core instruction

When forced to choose between sounding sophisticated and making the experimental logic obvious, choose clarity.

The desired paper should feel as though there is only one natural order in which the information could have been presented.
