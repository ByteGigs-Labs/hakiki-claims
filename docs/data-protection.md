# Data protection design note

Hakiki checks claims for a health fund, so everything it stores is health-adjacent personal data. This note says what is stored, what is not, and what is built versus planned. It is a design note and not legal advice. A Kenyan data-protection practitioner should review it before any real patient data is processed.

**Status key:** **Built** means it exists in the code and has tests. **Planned** means designed but not built.

## What Hakiki stores

| Data | Where | Notes |
|---|---|---|
| Patient token | `claims_checked.patient_token`, audit payload | A keyed HMAC-SHA-256 of the facility's patient identifier. The raw identifier is replaced before validation completes and is never written to the database or the logs. **Built** |
| Claim facts | `claims_checked`, audit payload | Reference, facility, service code, fund, date of service, amount, member status, ICD-10 code, pre-authorisation and referral references. **Built** |
| Check result | audit payload | Verdict, truth values, trace, fixes, rulebook version. **Built** |
| Users | `users` | Name, email, Argon2 password hash, role. **Built** |
| Sessions and API keys | `sessions`, `api_keys` | Only SHA-256 hashes of the tokens. **Built** |
| Uploaded CSV rows | `batches.claims` | Held only while a batch is processed, then emptied. **Built** |

## What Hakiki does not store

Patient names, national identifiers, phone numbers, clinical notes, diagnoses beyond the ICD-10 code, and the CSV file itself. The service cannot turn a token back into a person without the facility's own records and the deployment's HMAC key.

## Controls that exist

- **Pseudonymisation** at the point of entry (`ingest/pseudonymise.py`), tested so the raw identifier cannot appear in a response, a row or a log record.
- **Logs without identifiers:** structured logs hold the method, path, status, duration and a request ID. A redaction filter removes bearer tokens, session cookies and long opaque strings. A test posts a claim with a raw identifier and fails if it appears in any log record.
- **Tenant isolation:** every query is scoped by tenant, and tests cover cross-tenant access.
- **Access control:** clerk, finance manager and admin roles; API keys act as a clerk and reach only the check, explanation and batch endpoints.
- **Tamper-evident audit log:** hash-chained per tenant, protected by a database trigger that blocks updates and deletes.
- **Transport and browser security:** TLS and HSTS through Caddy in the production stack, a strict content-security policy, `HttpOnly` `SameSite=Strict` session cookies.
- **Rate limits and body limits** on login, checks, batches and password changes.

## Retention

| Data | Rule | Status |
|---|---|---|
| Audit log | Kept for the life of the contract, because it is the proof of what Hakiki advised. Holds tokens, not identities. | By design |
| Claims history | Kept for the contract term plus the period the facility needs for payer disputes (to be agreed with each facility). | **Planned:** a per-tenant retention setting and a scheduled purge of `claims_checked` |
| Sessions | Expire after 12 hours. | **Built** |
| Backups | Daily dumps kept for 14 days, readable only by the owner (`infra/backup.sh`). | **Built** (script). **Planned:** encrypt dumps and store a copy off the host |

## Erasure and access requests

The audit log is append-only, so Hakiki does not edit it. Because it contains tokens and not identities, an erasure request is met in two steps:

1. The facility removes the link between the person and the token in its own records. Without it, the stored token identifies nobody.
2. Hakiki deletes the matching `claims_checked` rows for that token on the facility's written request. **Planned:** an admin command for this. Until it exists, the request is handled by a documented database procedure run by a named operator.

If a deployment needs stronger guarantees, rotating the HMAC key for a tenant makes every old token unlinkable to newly submitted claims. The trade-off is that duplicate detection no longer matches across the rotation.

An access request is answered from `claims_checked` and the audit log by token, with the facility confirming the person's identity.

## Breach process

1. **Contain:** revoke sessions and API keys, rotate the HMAC key if it may be exposed, and isolate the host.
2. **Assess:** use the audit chain and request logs (which carry no identifiers) to see which tenants and tokens were touched.
3. **Notify:** tell affected facilities, who are the data controllers, without undue delay, and support them in notifying the Office of the Data Protection Commissioner within 72 hours of becoming aware, as the Data Protection Act 2019 requires of controllers.
4. **Learn:** record the cause and the fix, and add a test.

Roles for this process (incident lead, facility contact, regulator contact) are to be named before the first pilot.

## Roles

The facility is the data controller. ByteGigs Labs acts as a data processor under a written processing agreement. **Planned:** a template agreement and registration with the ODPC as required.

## DPIA outline

A data protection impact assessment is needed before processing real data. Outline:

1. **Purpose:** reduce avoidable claim rejections. No profiling of patients; the unit of analysis is a claim.
2. **Necessity and proportionality:** only the fields the rules need are used, and identifiers are pseudonymised on arrival.
3. **Risks:** re-identification of tokens by a party holding the facility's records and the key; insider access; breach of the hosting environment; a wrong verdict causing a lost claim.
4. **Mitigations:** the controls above, human review of every verdict, a visible trace and citation, and no automated submission to the payer.
5. **Residual risk and sign-off:** to be completed with the facility and a practitioner.

## Hosting plan

Production hosting is not decided. The requirement is that health data is processed in line with the Data Protection Act 2019, its regulations and the Digital Health Act 2023, including any localisation duties. The shortlist to assess is a Kenya-based data centre and a cloud region with a local presence. The stack in `infra/` and `docker-compose.prod.yml` is portable, so the decision does not change the code. Nothing is deployed until this review is done.
