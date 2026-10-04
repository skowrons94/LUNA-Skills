---
name: methods-paper-style
description: Write or revise nuclear-physics methods and R-matrix papers in the style of C. R. Brune and R. J. deBoer (PRC, RMP, NIM A) — plain first-person-plural exposition, every symbol defined where it appears, assumptions and neglected effects stated with their size, conventions made explicit, balanced treatment of alternatives, and conclusions that say what was clarified and what remains open. Use when drafting or editing formalism sections, method descriptions, R-matrix analyses, validation sections, or conclusions of a technical nuclear-physics or nuclear-astrophysics paper, or when asked to make a manuscript "more scientific" in this register.
---

# Brune–deBoer style

Distilled from Brune, *Formal and Physical R-matrix parameters* (2005); Brune &
Sayre, NIM A 698, 49 (2013); Brune & deBoer, PRC 102, 024628 (2020); Brune et al.,
PRC 50, 2205 (1994); deBoer et al., PRC 91, 045804 (2015); deBoer et al., RMP 89,
035007 (2017); deBoer et al., PRC 103, 055815 (2021).

The reader is a working physicist who will reuse the result. Every sentence
serves one of three purposes: state what is done, state under which
assumptions, or state what it means. Nothing is there to persuade.

## 1. Voice

- **First person plural, active, present tense** for what the paper does:
  *"We consider here a nuclear reaction sequence…"*, *"In this paper, we present
  a general framework for…"*, *"We are particularly interested in situations
  where…"*. Past tense only for what was measured or computed.
- **Plain declaratives, moderate length.** One idea per sentence; a second
  clause only to qualify the first. No rhetorical questions except the one that
  states the problem (see §2).
- **Temperate adjectives.** *important, significant, useful, convenient,
  straightforward, relatively small, very feasible.* Never *dramatic, striking,
  crucial, the wrong tool, in all but name, trap*. Strength comes from the
  number, not the adjective.
- **Signposting words used sparingly and literally:** *In practice*, *in
  principle*, *Note also that*, *It should be noted that*, *Fortunately*,
  *However*, *Therefore*, *Thus*, *In other words*. At most one per paragraph.
- **Credit and disagreement are courteous.** *"It is, however, but one of many
  valid approaches, and, in some circumstances it has some distinct
  disadvantages."* Name the reference, state the limitation, move on.
- No em-dash chains, no italics for emphasis, no bold in running text.

## 2. Architecture

**Abstract** (3–5 sentences, or the PRC structured Background / Purpose /
Methods / Results / Conclusion for experimental papers): what is lacking, what
the paper supplies, how it is demonstrated. *"…a practical formalism … has never
been given. … This paper supplies the needed framework, and it is demonstrated
by the application to …"*

**Introduction**, four moves:
1. The general setting in one or two sentences, stated as accepted fact.
2. The specific gap, stated concretely — often as a missing capability or an
   inconsistency in the literature, with values and references
   (*"the S factor at solar energies remains uncertain to at least 7% [5]"*).
3. The purpose: *"The purpose of this paper is to describe how…"* /
   *"This paper provides the necessary formalism to make this type of analysis
   possible."* Optionally the problem as one question: *"The question we want to
   address here is: how does one …? In other words, …"*
4. The roadmap, one sentence per section: *"This paper is organized as follows.
   First, … It is then specialized to … We then further specialize … Finally,
   we discuss …"*

**Formalism / method**: start from the most general statement, cite where it
comes from, then specialize step by step to the case used. Each specialization
is announced (*"It is often the case that only one multipole is present … In
this situation …"*).

**Application**: introduced as a demonstration of the method, not as a result
in itself (*"This dataset provides an opportunity to demonstrate …"*).

**Conclusions**: restate the abstract in the past tense in two sentences, then
say what the work *clarified* and what it did not: *"This analysis has
clarified what can, and what cannot, be explained by …"*; then what remains to
be done and by what kind of measurement: *"… several other issues remain that
make large contributions to the uncertainty, which must be addressed by further
capture and lifetime measurements."* End with the expected use: *"We expect
that these results will be useful for future analyses, including …"*

## 3. Equations

- Introduce an equation with what it is, then the equation, then **"where …"
  defining every new symbol in the order it appears**, in one sentence:
  *"where c (c′) label the incoming (outgoing) channel, k_c is the incoming
  wave number, … and Γ is given by the sum over all channels of the partial
  widths."*
- Give the source of borrowed results **to the equation**: *"[22, Eqs. (10.127),
  (10.130), and (10.131)]"*, *"see LT, Eq. III.4.5"*, *"Sec. XII.3(a) of LT"*.
- Refer back by number: *"By using Eq. (6) one can show that these
  transformations leave … invariant."*
- State normalization and range conventions right after the equation
  (*"normalized such that Σ g_L² = 1"*, *"k only takes even values"*).
- Put global conventions in a footnote at first use: *"We utilize laboratory
  energies throughout this paper, unless otherwise indicated."*

## 4. Assumptions, scope and neglected effects

This is the core of the style. Every approximation is stated where it is made,
together with its consequence and, when possible, its size.

- *"Here, we assume the state B decays via γ-ray emission 100% of the time to
  state C. If this is not the case, the above expression must be multiplied by
  the appropriate branching-ratio factor."*
- *"This factorization assumes that the process is sequential … photon emission
  is typically four or more orders of magnitude less likely than nuclear
  emissions … These order-of-emission effects are not an issue for any of the
  reactions mentioned in this paper."*
- Out-of-scope effects are named and dismissed in one sentence: *"Since the
  nature of these effects depends upon the details of the particular
  experiment, we will not consider them further here."*
- Conventions that others may misuse get an explicit caution, often as a
  numbered pair: *"it is very important to (1) understand what conventions are
  used by others if you use their results and (2) supply enough information so
  that others may properly use your results."*
- When several correct approaches exist, say so and compare them rather than
  crowning one: *"There are many potentially correct approaches to the
  problem; the relative merits of some of them are discussed."*

## 5. Results and uncertainties

- Quote numbers with their uncertainty and the reference they come from; give
  the range of competing values when the literature disagrees
  (*"Γ_γ = 0.41 (+34 −13) eV [14], 0.95 (+60 −95) eV [15], >0.85 eV [16]"*).
- Explain a mechanism with the smallest formula that captures it
  (*"σ_interference ∝ 2√(σ₁σ₂). Therefore even if one of the cross section
  components is small, the interference term can still be significant"*).
- Distinguish kinds of uncertainty explicitly (statistical, normalization,
  energy calibration, model) and say which one a given dataset constrains
  (*"While the relative cross sections do not provide as much constraint as
  absolute measurements, they greatly reduce the dependence of the data on
  otherwise significant systematic uncertainties"*).
- A fit result is reported with what it does and does not establish. Avoid
  "confirms", "proves"; prefer "is consistent with", "supports", "gives more
  confidence in", "does not determine".
- Emphasize the combination of data types: the R-matrix model is constrained
  only by using as many channels and observables as possible, and the text says
  which dataset constrains which parameter.

## 6. Anti-patterns to remove when revising

| Instead of | Write |
|---|---|
| "X is the wrong tool for Y" | "X requires …, which is not the case for Y" |
| "a fit parameter in all but name" | "is then effectively an additional adjustable parameter" |
| "This is a trap specific to ratio observables" | "For a ratio observable, a relative uncertainty is not appropriate because …" |
| "worth far more", "buys", "tells" | "reduces the uncertainty by …", "constrains", "indicates" |
| Passive agentless "it was found that" | "We find that" / "The fit gives" |
| A symbol defined two paragraphs later | "where …" immediately after the equation |
| "(see below)" for an assumption | the assumption, stated where it is used |
| Stacked hedges ("may possibly suggest") | one hedge, or a number |
| A result without its conditions | the result plus "under the assumption that …" / "for the adopted …" |
| Colon-and-semicolon chains | two sentences |

## 7. Revision checklist

1. Does the introduction contain setting → gap → purpose → roadmap?
2. Is every equation followed by "where …" defining each new symbol?
3. Is every borrowed result cited to the equation or section?
4. Is every approximation stated where it is made, with its size or the reason
   it is negligible for the cases treated?
5. Are conventions (frames, units, phase and coupling conventions) stated once,
   early, and in a footnote if global?
6. Are alternatives acknowledged with their merits?
7. Does each result say what it establishes and what it does not?
8. Do the conclusions say what was clarified, what remains open, and what
   measurement or analysis would close it?
9. Are there any evaluative adjectives or metaphors left? Replace with numbers.
10. First person plural throughout; no "I" except in lecture notes.
