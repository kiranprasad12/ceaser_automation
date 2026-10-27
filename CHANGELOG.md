# Changelog

All entries on this branch are DUMMY example work to test the push and branch workflow.

## Unreleased (test branch)

- `iso2cii.py`: branch outlets, line-thickness detection, per-size wall thickness (5S/10S/40S/80S), and joining of sheets that continue into each other (any line numbers) into one .CII. Sample-PDF results and open problems: `docs/RESULTS.md`. Tested in a sandbox only, not yet in CAESAR II.

- Added `units.py`: pressure to kPa and temperature to degrees C helpers.
- Added `line_number.py`: line number matching that ignores spaces, quotes and the size prefix.
- Added unit tests in `tests/`. Run them from the repo folder with `python -m unittest`.

## v1

- Latest `iso2cii.py` and `README.md` (see `main`).
