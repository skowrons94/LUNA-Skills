---
name: methods-paper-style
description: Write or revise technical nuclear-physics methods and R-matrix papers in a plain, reusable register — first-person-plural exposition, every symbol defined where it appears, assumptions and neglected effects stated with their size, conventions made explicit, balanced treatment of alternative approaches, and conclusions that say what was clarified and what remains open. Use when drafting or editing formalism sections, method descriptions, R-matrix analyses, validation sections, or conclusions of a technical nuclear-physics or nuclear-astrophysics paper, or when asked to make a manuscript "more scientific" in this register.
---

# Methods-paper style

The reader is a working physicist who wants to reuse the result. Every sentence should do one of three things: say what is done, say under which assumptions, or say what the result means. Nothing is there to persuade.

## 1. Voice

- **First person plural, active voice, present tense** for what the paper does; past tense only for what was measured or computed.
- **Plain declarative sentences of moderate length.** One idea per sentence; add a second clause only to qualify the first. The only question in the paper, if any, is the one that states the problem.
- **Temperate adjectives** (important, significant, useful, convenient, relatively small). Avoid dramatic or colloquial wording and metaphors. Let numbers carry the strength of a statement.
- **Signposts used sparingly and literally** (in practice, in principle, note that, however, therefore, thus, in other words); about one per paragraph at most.
- **Courteous treatment of other work.** Cite the approach, state its limitation for the case at hand, and continue. Acknowledge that it may be the better choice in other situations.
- No chains of dashes, no italics or bold for emphasis in running text.

## 2. Architecture

**Abstract.** Three to five sentences (or the journal's structured format): what is missing, what the paper provides, how it is demonstrated.

**Introduction**, in four steps:
1. The general setting, briefly, as accepted fact.
2. The specific gap, stated concretely: a missing capability, or an inconsistency in the literature with values and references.
3. The purpose of the paper in one sentence. Optionally, the problem as a single explicit question followed by a plain restatement.
4. A roadmap with one sentence per section.

**Formalism or method.** Begin from the most general expression, cite its origin, and specialise step by step to the case actually used. Announce each specialisation and the condition under which it holds.

**Application.** Present it as a demonstration of the method, not as the result in itself.

**Conclusions.** Summarise what was done in a sentence or two, then say what the work clarified and what it did not, which open issues dominate the remaining uncertainty and what kind of measurement or analysis would address them, and how the results are expected to be used.

## 3. Equations

- Say what an equation is, give it, and follow it with a single "where ..." sentence that defines every new symbol in the order it appears.
- Cite borrowed results to the specific equation or section of the source, not only to the work.
- Refer back to equations by number.
- State normalisation and range conventions right after the equation they apply to.
- Put conventions that hold throughout (energy frame, units, phase conventions) in one place early, for example a footnote at first use.

## 4. Assumptions, scope and neglected effects

This is the core of the register. State each approximation where it is made, together with its consequence and, when possible, its size.

- When a formula assumes a simplification (for example a 100 % branching or a sequential process), say so next to the formula and say how the result changes if the assumption fails.
- When an effect is neglected, give the reason in one sentence: an order-of-magnitude estimate, or the observation that it does not arise for the cases treated.
- Name effects that are out of scope and explain briefly why they are not treated.
- Where conventions are easily misused, add an explicit caution: readers should check the conventions behind results they adopt, and authors should give enough information for others to use theirs.
- When several correct approaches exist, say so and compare their merits instead of declaring one the only valid choice.

## 5. Results and uncertainties

- Quote each number with its uncertainty and source. When the literature disagrees, give the range of reported values with references.
- Explain a mechanism with the smallest formula that captures it (for example, the scaling of an interference term with the component amplitudes).
- Distinguish kinds of uncertainty (statistical, normalisation, energy calibration, model) and say which dataset constrains which.
- Report a fit result together with what it establishes and what it does not. Prefer "is consistent with", "supports", "does not determine" to "confirms" or "proves".
- In R-matrix work, use as many channels and observables as possible and say which dataset constrains which parameter.

## 6. Patterns to replace when revising

| Instead of | Write |
|---|---|
| A verdict ("X is the wrong tool for Y") | The condition X requires and why Y does not meet it |
| A colloquial label for a parameter | What the parameter effectively becomes (for example, an additional adjustable parameter) |
| Value-laden verbs ("buys", "tells", "is worth far more") | "constrains", "reduces the uncertainty by ...", "indicates" |
| Agentless passive ("it was found that") | "We find that" / "The fit gives" |
| A symbol defined paragraphs later | "where ..." immediately after the equation |
| "(see below)" for an assumption | The assumption, stated where it is used |
| Stacked hedges ("may possibly suggest") | One hedge, or a number |
| A result without its conditions | The result plus the assumption or adopted input it depends on |
| Long colon-and-semicolon chains | Two sentences |

## 7. Revision checklist

1. Does the introduction contain setting, gap, purpose and roadmap?
2. Is every equation followed by a "where ..." clause defining each new symbol?
3. Is every borrowed result cited to the equation or section?
4. Is every approximation stated where it is made, with its size or the reason it is negligible here?
5. Are conventions (frames, units, phase and coupling conventions) stated once, early?
6. Are alternative approaches acknowledged with their merits?
7. Does each result say what it establishes and what it does not?
8. Do the conclusions say what was clarified, what remains open, and what would close it?
9. Are evaluative adjectives or metaphors left? Replace them with numbers.
10. First person plural throughout; singular only in lecture notes or single-author commentary.
