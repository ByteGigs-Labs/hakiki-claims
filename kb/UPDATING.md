# Updating the rulebook

SHA changes its rules through circulars, regulations and tariff schedules. A change must be reviewable, versioned and provable. Follow these steps for every change.

1. **Read the source.** Save the new document in `docs/sources/` and add it, with its SHA-256, to `docs/sources/SOURCES.md`.
2. **Edit the rule.** Change the rule in `kb/rules/` or the data in `kb/reference/`. Update its entry in `kb/citations.json` with the new quote, section and effective date. Set `verified` to `true` only when the quote was read in the saved document.
3. **Adjust truth values** only with a reason. Update `kb/rules/truth-values.md` in the same change. `python -m reasoner.calibrate` shows how a rule has performed on real outcomes.
4. **Bump `kb/VERSION`.** Every stored check records the version it ran under, so an old verdict can still be explained as of its date.
5. **See the impact.** Run `python -m reasoner.impact --base origin/main`. It replays the synthetic claims on both rulebooks and lists every claim whose verdict, strength or firing rules changed. Paste it into the pull request.
6. **Update the expectations.** If the changes are intended, update `data/synthetic/expected.csv` (through `scripts/build_synthetic.py`) and the pinned hash in `tests/golden/test_golden.py`, and add a test for the new behaviour.
7. **Open the pull request.** CI runs the impact report on every pull request, shows it in the job summary, and fails when the rules changed and `kb/VERSION` did not.

Documentation-only changes (`truth-values.md`, `LICENSE`, this file) do not need a version bump.
