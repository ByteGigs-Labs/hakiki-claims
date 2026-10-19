# Three-minute demo script

Run it on the seeded demo account (`python -m scripts.seed`) with synthetic data only. Rehearse twice and keep the timings.

## 0:00 – 0:20 · The problem

"Kenyan facilities lose revenue every month to rejected SHA claims, and the reasons are buried in rules billing staff cannot see. Hakiki tells you *before* you submit which rule a claim would fail, why, and how to fix it."

## 0:20 – 1:00 · A week of claims in one pass

1. Open **Batch check** and drop in `data/synthetic/claims.csv`.
2. Watch the progress ring, then point at the revenue card: "44 claims, KES at risk, and the rules that cause most of the failures".
3. Filter to **Will fail**. Say: "Several different rules appear here, and every one is cited."

## 1:00 – 2:10 · One claim, fully explained

1. Open the caesarean claim without pre-authorisation, or press **Sample** on **Check claim** and check it.
2. Point at the verdict (`Will fail`), the truth value, and the revenue at risk.
3. Walk the trace: "Eleven checks, ten passed. R3 failed." Click **Source R3** and read the quote from Regulation 60.
4. Click **Apply** on the pre-authorisation fix. The form fills a placeholder, the claim re-checks, and the verdict flips to **Will pass**. Say: "The fix was proven by running the rules again, and the field is flagged as a placeholder until the clerk enters the real reference."
5. Switch the explanation to **Kiswahili**: "The language model only explains. It cannot change the verdict."

## 2:10 – 2:30 · Reproducible and auditable

Click **Run the same claim again**. "Same claim, same rulebook, identical trace hash. Every check is chained into a tamper-evident log, so a facility can use it when it appeals."

## 2:30 – 2:45 · The money

Open **Overview**: "This is what Hakiki caught before SHA did. Claims fixed before submission are revenue protected, and the rest shows what is still at risk and why."

## 2:45 – 3:00 · Evidence, model and ask

- Read the clinic quote captured in the interviews (add it here once collected).
- "Health data is pseudonymised on arrival. The rulebook is versioned and every rule cites the regulation it comes from. Pricing starts with a per-facility subscription paid by M-Pesa."
- Ask: design partners to run Hakiki on live claims and calibrate the truth values.

## Checklist

- [ ] Every verdict shows its trace and a SHA citation
- [ ] Live fix flips the verdict to pass
- [ ] Identical trace hash on re-run
- [ ] Say clearly that the language model explains and never decides
- [ ] Synthetic data only
- [ ] One real clinic quote
