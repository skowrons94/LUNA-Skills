# Direct IAEA NDS access

Official reference: [LiveChart API guide](https://www-nds.iaea.org/relnsd/vcharthtml/api_v0_guide.html). The client uses `https://www-nds.iaea.org/relnsd/v1/data` with explicit query parameters and a User-Agent. No `nudel` installation is required.

```
python scripts/nds.py fetch 60co --fields decay_rads --out nds-co60
python scripts/nds.py lines nds-co60/data.csv --parent-energy-keV 0 --decay B- --out co60-lines.json
python scripts/nds.py fetch 60ni --fields gammas --out nds-ni60
python scripts/nds.py fetch 60ni --fields levels --out nds-ni60-levels
```

Decay radiation queries request gamma rays. Select parent state and decay mode explicitly: one table can contain ground and metastable parents. Gamma energies are in keV and intensities are percentages; blank values are unknown. Adopted gamma transitions and parent decay radiation tables answer different questions. Retain evaluation/extraction dates and uncertainty/qualifier columns; retrieval date does not establish evaluation freshness.

The client stores untouched CSV plus request URL, UTC retrieval time and SHA256 metadata. It rejects API error/HTML responses and refuses to overwrite a cache directory. Reuse a snapshot for reproducibility; refetch to a new directory when updating. No network failure is converted to invented data.

For cascades, link `start_level_idx` and `end_level_idx` to level identifiers. Verify level lifetimes against the acquisition coincidence window. Conversion, missing branches, uncertain intensities and competing decay modes need explicit treatment. `nds_scheme.py` constructs a conditional electromagnetic graph only after the caller supplies `--assume-complete-em`; this flag is a scientific assumption, not a data-quality verdict.

```
python scripts/nds_scheme.py nds-ni60/data.csv --start-level-idx 4 --assume-complete-em --out conditional-ni60.json
```

The converter weights branches by relative gamma intensity times `(1+ICC)` and sets gamma emission probability to `1/(1+ICC)`. Missing ICC errors by default; `--missing-icc zero` is an explicit recorded approximation. Do not confuse the resulting conditional initial population with beta feeding per source decay. Inspect the saved source rows and assumptions before using the scheme.
