# Truth values

Every rule returns `(stv strength confidence)`. **Strength** says how strongly the rule's outcome holds, and **confidence** says how much evidence backs that number. Both are expert-set for v1 and need calibration against real accept/reject outcomes from design partners.

| Rule | Outcome | stv | Why |
|---|---|---|---|
| R1 eligibility | active | 1.0, 0.9 | The status is supplied by the facility from the SHA portal, so it is trusted but not independently verified. |
| | inactive | 0.95, 0.9 | An inactive member is the clearest rejection cause in published reporting. |
| | unknown | 0.6, 0.6 | The status was not confirmed. This is a risk, not a certain failure. |
| R2 contract | contracted | 1.0, 0.9 | The demo registry is synthetic, so confidence stays below 1. |
| | not contracted | 0.95, 0.9 | An uncontracted provider's claims are not payable. |
| | unknown facility | 0.7, 0.5 | The registry may simply be incomplete. |
| R3 pre-auth | missing | 0.95, 0.92 | Regulation 60 makes pre-authorisation a condition for specialised services. Confidence is highest here because the rule is binary and checkable. |
| | emergency | 1.0, 0.9 | Regulation 60(3) exempts emergency services. |
| | present | 1.0, 0.9 | Hakiki checks presence only. It cannot confirm the reference is valid. |
| R4 coverage | not covered | 0.9, 0.85 | Package membership is binary, but the demo package list is a subset. |
| | unknown service | 0.8, 0.6 | A code outside the rulebook is probably uncovered, but may be a gap in the rulebook. |
| R5 level | too low | 0.9, 0.9 | KEPH levels are fixed per facility. |
| R6 tariff | over cap, published tariff | 0.9, 0.85 | Payment is capped at the tariff. Only the two Primary Healthcare Fund maternity rates were read from SHA's published schedule. |
| | over cap, placeholder tariff | 0.9, 0.55 | Same rule, but the cap is an illustrative placeholder, so confidence drops. The trace marks it "Placeholder cap". |
| | within cap | 1.0, 0.9 or 0.6 | Confidence follows the same published-versus-placeholder split. |
| R7 documentation | no diagnosis code | 0.5, 0.7 | Form 3 requires clinical details, but another field might carry them, so this is a risk and not a failure. |
| R9 clinical | inconsistent | 0.6, 0.6 | ICD-10 chapters are standard clinical groupings, not SHA's own mapping, so it is a warning only. |
| R10 timely lodging | late | 0.7, 0.7 | Regulation 58(1) sets a seven-day duty without stating the consequence of lateness. |
| R11 referral | missing | 0.65, 0.6 | Regulation 10(b) buys Social Health Insurance Fund services on referral, but the Act's section 27 detail was not available. |
| R8 duplicates | duplicate | 0.95, 0.85 | Same patient, service and date under a different reference. |
| | frequency | 0.85, 0.8 | Frequency windows are approximations of the rule text. |

## Combining

`kb/combine.metta` folds the results and ignores `skip`:

- **WILL_FAIL** when the strongest risk (`fail` or `warn`) has strength **0.8 or more**.
- **AT_RISK** when there is any other risk.
- **PASS** otherwise.

For a failing or at-risk verdict the strength is the noisy-or of the risk strengths, `1 - ∏(1 - sᵢ)`, and the confidence is the lowest confidence among the risks. For `PASS` both values are the weakest among the passing rules, so a pass is only as strong as its weakest check.

## Calibration

`reasoner/calibrate.py` compares what the rules predicted with what a payer really did. It is a command-line tool, needs no database, and never edits `kb/`.

```bash
python -m reasoner.calibrate --claims claims.csv --outcomes outcomes.csv --report report.json
```

`claims.csv` uses the batch columns. `outcomes.csv` has `claim_ref` and `outcome` (`accepted` or `rejected`). Rows are replayed in file order, so earlier rows count as history for the duplicate rule. `data/synthetic/outcomes.csv` is an invented example made by `python -m scripts.build_outcomes` with a fixed seed; it shows the format and proves nothing about real payers.

Per rule the table shows:

- **fired**: how often the rule returned `fail` or `warn`.
- **rejected**: how many of those claims were then rejected. `rejected / fired` is the precision.
- **missed**: rejections where this rule stayed quiet. A large number is normal, since other rules usually explain those claims.
- **current**: the average strength the rule used when it fired.
- **suggest**: `(rejected + 5 × current) / (fired + 5)`. The expert value counts as five observations, so a handful of claims cannot swing it far.
- **conf**: `fired / (fired + 5)`, capped at 0.95. It grows with the number of claims seen and never claims certainty.

Treat a suggestion as a prompt to look, not an instruction. Wait for 30 or more firings per rule before changing a number, read the rejected claims, and then follow the steps below.

## Changing a truth value

1. Edit the stv in the rule file and in the table above.
2. Re-run the golden tests, since trace hashes change when truth values do.
3. Bump `kb/VERSION`.
