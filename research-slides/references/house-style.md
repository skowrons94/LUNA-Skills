# House style

Measured from the user's own conference, seminar and working-group decks (2025–2026). Values are in inches on a 13.33 × 7.50 in (16:9) canvas unless stated.

## Choose the variant

| Variant | Use for | How |
|---|---|---|
| **House layout** (default) | Conference talks, invited talks, seminars, technical meetings | `Deck()`; drawn by `deck.py`, no template file |
| **User template** | When the talk must use an institutional or collaboration master the user is entitled to use | `Deck(template="path.pptx")`; keeps its masters, fonts and footer |
| **Working-group note** | Small internal updates, feasibility discussions | the user's WG deck as a custom template; 10 × 5.62 in, white, Cambria titles in orange-red `#C25E2E`, Calibri body, thin warm-grey footer rule |

Keep one variant per deck. No logos or institutional templates are bundled with this skill; logos, badges and watermarks are optional image paths supplied by the user.

## House layout

### Frame

- **Header bar**: red `#AA0004` band across the top, 0.75 high.
- **Title**: in the bar, white, bold, Arial 20 pt, left-aligned from x 0.5. Keep titles to one line (about 60 characters).
- **Badge**: optional small image (`badge=path`) at the right end of the bar, 0.7 × 0.66, marking which part of the talk a slide belongs to.
- **Footer**: thin grey rule at y 7.06; footer text at y 7.09, 10 pt grey, e.g. "Name  |  Institute  |  EVENT"; page number 10 pt grey at x 12.4, y 7.08. Build steps share one page number.
- **Body**: y 0.95 to 6.95. Background white.

### Title, divider and closing slides

- **Title slide**: full red background. Title in **Cambria bold 32 pt white**, two lines maximum; subtitle italic 16 pt with the reaction; name 28 pt, affiliation 14 pt, event bold 20 pt and date/venue below. Optional user logos (`logos=[...]`) in the lower middle and an optional faded watermark (`deck.watermark(slide, path)`).
- **Section divider**: same red background, section title bold 40 pt white at the left ("Part 1: Direct measurement"), optional logo image on the right.
- **Closing**: "Thank you" bold 40 pt, one line naming the collaborations, optional row of logos. Then a "Backup" divider and backup slides with titles "Backup — …".
- **Animation slides**: full-bleed video on navy `#0B1220`, no header, no footer.

### Typography

| Element | Font / size | Colour |
|---|---|---|
| Body bullets | Arial 18 pt (16–20), line spacing ≈1.1, 6–8 pt after | `#393D3F` |
| Emphasis | **bold** of the key phrase, not of whole bullets | same |
| Accent inside text | sparing; red `#AA0004` for the one word that matters | |
| Figure source line | 12 pt italic, centred under the figure | grey `#6E7376` |
| Card headers | 16 pt bold white on a coloured bar | |
| Card body | 15 pt | `#393D3F` on `#F2F2F2` |
| KPI value | 34 pt bold white | on red or grey |
| Callout bar | 22–24 pt bold white, centred | on red rounded bar |
| Equations | LaTeX or Cambria Math, 24–32 pt | `#393D3F` |

Minimum on-screen size is 14 pt except footers, page numbers and source lines.

### Colour semantics

- Red `#AA0004`: the result, "this work", the take-away. Use it for the fitted model and "This work" points in plots too, so the figure and the callout agree.
- Grey `#6E7376`: the previous state of knowledge (e.g. "8.4 %, Solar Fusion III" before "X %, This work").
- Blue `#1F4E79` / green `#2E7D32` / red: the three parallel columns of a comparison or summary (e.g. Direct / Indirect / Impact).
- Orange `#FF7D0D`: secondary annotation inside figures and equations (which detector provides which term).
- Plots otherwise keep Matplotlib's tab10 order; keep a dataset's colour fixed across all slides.

## Component catalogue

Each component below appears repeatedly in the user's decks; `deck.py` implements it.

| Component | Where it is used | `deck.py` |
|---|---|---|
| Figure left (≈6.9 × 4.3), 3–4 bullets right (x 7.7, w 5.1) | The standard evidence slide | `s.figure(path, LEFT_FIG)`, `s.bullets(items, RIGHT_TEXT)` |
| Source line under a borrowed figure | "Borexino, Nature 587 (2020): first detection of CNO neutrinos" | `figure(..., caption=...)` or `s.caption()` |
| Take-away bar | Last build step of a slide: "The 6.79 MeV state is both the strongest transition and the sub-threshold resonance of the ground-state transition." | `s.callout(text)` |
| Big number | "8.4 % — uncertainty on S₁₁₄(0) — Solar Fusion III (2025)" | `s.kpi(value, label, source)` |
| Before → after | Grey "8.4 %" (literature) → red value of this work | `s.kpi_transition(before, after)` |
| Coloured cards | Summary in three columns; "What SF III asks for" in two | `s.cards([(header, colour, bullets), ...])` |
| Person credit | Photo + credit line ("A. Student, PhD work") beside the setup of a student's measurement | `s.person(photo, caption)` |
| PRELIMINARY | Light grey diagonal text over unpublished results | `s.preliminary(box)` |
| Annotated equation | Doppler formula with coloured circles on β and cos θ and labels naming which detector provides each term; yield equation with labels under each factor (counts, cross section, efficiency, current) | `s.equation(...)` + `s.box_outline(...)` + `s.text(..., color=ORANGE)` |
| Arrows from text to figure feature | Pointing at the peak, the gap in data, the bottleneck | `s.arrow(x1, y1, x2, y2)` |
| Section divider | Before each part of the talk | `d.section(title, logo)` |
| Full-bleed animation | Opening hook, the method explained in motion | `d.video(mp4, poster)` |

Tables of numbers are typeset (LaTeX or PowerPoint table) with flat rules and no fills; references in blue link colour. Keep units in every column header and the energy frame (lab or c.m.) explicit on every axis.

## Figures

- Figures carry the slide; text explains what to notice. Prefer one main figure or two that are directly compared.
- Export at the size used on the slide with `assets/slides.mplstyle` (16–17 pt labels at 6.9 × 4.3 in, 250 dpi), white background. Borrowed figures: highest resolution available, with the source line.
- Put the legend inside only if it covers no data. Mark the signal window, energy region or angular selection the claim depends on.
- Reuse the same figure across build steps; add overlays (outline, arrow, callout) instead of re-exporting variants.
