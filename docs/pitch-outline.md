# Pitch outline

Ten slides, about five minutes. Numbers in [brackets] come from the clinic interviews, so fill them in before presenting.

| # | Slide | What to say | Evidence |
|---|---|---|---|
| 1 | **Hakiki** | One line: "Know before you submit. A glass box pre-audit for SHA claims." | Logo, tagline |
| 2 | **The problem** | Facilities lose revenue every month to rejected and delayed SHA claims, and the reasons are buried in rules clerks cannot see. | [KES lost per rejection], [share of claims rejected], quotes |
| 3 | **What we heard** | The three biggest pains from the interviews, in the clinics' own words. | `docs/interviews.md` summary |
| 4 | **The idea** | Check every claim before it is submitted. Show which rule it fails, the regulation behind it and the smallest fix. | Screenshot 03 |
| 5 | **The glass box** | Eleven rules in MeTTa, each with a truth value and a citation. The same claim always gives the same trace and hash. | Screenshots 04 and 05 |
| 6 | **Live demo** | Batch upload, one claim explained, fix to pass, Kiswahili, Overview. Three minutes. | `docs/demo-script.md` |
| 7 | **Trust and compliance** | The language model explains and never decides. Patient data is pseudonymised on arrival. Tamper-evident audit log. DPA 2019 and the Digital Health Act are handled in the design. | README sections 10 and 11 |
| 8 | **Business model** | Starter, Hospital, Recovery and Partner API tiers, paid by M-Pesa. Hakiki costs less than the claims it saves. | README section 12, [price signals] |
| 9 | **Where we are** | Working product, 300+ automated tests, rulebook cited to the regulations, deployable stack. What is still illustrative: most tariffs and the facility registry. | `docs/sources/SOURCES.md` |
| 10 | **The ask** | Design partners to run Hakiki on live claims and help calibrate the truth values. | 90-day plan in the roadmap |

## Rules of thumb

- Lead with the clinics' pain, not the technology.
- Say plainly what is verified and what is illustrative. Judges trust that more than a perfect-looking demo.
- Show the fix flipping to pass live. It is the moment that makes the idea land.
