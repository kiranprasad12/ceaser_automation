# Branch rules

- `main` holds the latest working code. Only tested versions go here.
- `test` holds the new version under development.
- Nothing moves from `test` to `main` without approval from the owner.

## Moving a version from test to main

1. Run the tool on the sample PDFs on the `test` branch and check the results.
2. Get approval from the owner.
3. Merge `test` into `main`.
4. Keep the history. Do not squash away earlier versions.
