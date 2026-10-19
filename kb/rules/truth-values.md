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

## Calibration plan

1. Record the accept/reject outcome of every design-partner claim next to its verdict.
2. Per rule, compare predicted strength with the observed rejection rate and adjust the stv.
3. Re-run the golden tests after each change, since trace hashes change when truth values do. Bump `kb/VERSION` with every change.
