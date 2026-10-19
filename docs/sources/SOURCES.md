# SHA source documents

Public documents used to build and check the rulebook in `kb/`. Downloaded on **19 October 2026**. Each rule in `kb/citations.json` names the document and the regulation it relies on, with a short quote.

| File | Document | Downloaded from | SHA-256 |
|---|---|---|---|
| `shi-regulations-2024.pdf` | Social Health Insurance Regulations, 2024 (Legal Notice No. 49 of 2024), Kenya Gazette Supplement No. 60, 8 March 2024 | https://www.ramco.com/hubfs/SHI%20REGULATIONS%202024.pdf.pdf | `df9de62b7107bf7e41a7fb5fc6c17da8ab006b6e851d0b9fa5f4dfea656bf788` |
| `annexure-b1-phc-tariffs.pdf` | SHA Contract, Annexure B1-A: Primary Healthcare Fund Tariffs and Payment Rates | https://www.sha.go.ke/wp-content/uploads/2026/09/ANNEXURE-B1-A-Primary-Healthcare-Fund-Tariffs-Payment-Rates.pdf | `b2d7207b9e5de046d0e7e57bccb235a58cbffdbcd5f7c090c0ca78f691876278` |
| `shi-general-regulations-2023-draft.pdf` | Social Health Insurance (General) Regulations, 2023, an unnumbered draft | https://p4h.world/app/uploads/2024/04/SOCIAL-HEALTH-INSURANCE-GENERAL-REGULATIONS-2023.x23411.pdf | `def22e3a42ae8c2ce3b4f06631807c434d7c1fde05e765f550df8a5a524110ef` |

The regulations PDF is a third-party copy of the gazette. Compare it with the Kenya Gazette or Kenya Law before relying on it in a dispute.

## What was read, and what is missing

Read and used:

- **Regulation 57(1)**: benefits are paid to an empanelled and contracted facility, or to one licensed for emergency services (rule R2).
- **Regulation 60**: pre-authorisation for specialised services, with no pre-authorisation for emergencies (R3).
- **Regulation 58(1) and 58(4)**: lodge within seven days of discharge, and the contents of the claim form (R7, R10).
- **Regulations 6(3), 7(2) and 10(b)**: Social Health Insurance Fund services are bought on referral from primary facilities (R11).
- **Second Schedule**: the Primary Healthcare Fund package and its points of access (R4, R5).
- **Annexure B1-A section 2**: normal delivery KES 10,000 and caesarean section KES 30,000 under the Primary Healthcare Fund (R6, the only tariffs verified).

Not available, so the related data is illustrative:

- The Social Health Insurance (Tariffs for Healthcare Services) Regulations, Legal Notice 56 of 2025, as amended by Legal Notice 78 of 2026. The SHA annexure names them as the source of the rates. The 2024 tariff notice, Legal Notice 146 of 2024, returned a 404.
- The full text of the Social Health Insurance Act, 2023, including section 27 on referrals.
- SHA's list of specialised services that need pre-authorisation, and its diagnosis-to-service mapping.
- SHA's facility registry. The facilities in `kb/reference/facilities.json` are synthetic.

Replace the illustrative caps in `kb/reference/services.json` with the tariff schedule before any production use, and list each verified cap in `verified_tariffs`.
