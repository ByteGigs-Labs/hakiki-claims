# QA checklist

Run it on the live demo or a local `docker compose up` after `python -m scripts.seed`. File one GitHub issue per problem with the steps, what you expected and what happened, plus a screenshot. Tick the box only when it works.

Demo login: `clerk@demo.hakiki.test` with the password from your `.env`.

## Sign in

- [ ] A wrong password shows "Invalid email or password" and never says whether the email exists.
- [ ] Five wrong attempts for one account lock it for a few minutes. A correct password after that is refused until the lock ends.
- [ ] After signing in, finance managers and admins land on Overview, and clerks land on Check claim.
- [ ] Sign out returns to the sign-in page, and the back button does not show private pages.

## Check a claim

- [ ] **Sample** fills the form. **Check this claim** returns Will fail with 11 checks.
- [ ] Each form error appears on the right field and disappears when fixed (empty amount, date in the future, bad ICD code, bad reference).
- [ ] The service hint changes with the fund (level and pre-authorisation).
- [ ] The Pre-authorisation fix flips the claim to Will pass and shows the placeholder warning until the field is edited.
- [ ] **Apply all** works when a claim has two fixes.
- [ ] Each **Source R...** button opens the right rule, with a quote and a verification note.
- [ ] **Emergency service: Yes** makes pre-authorisation and referral pass.
- [ ] The explanation switches between English and Kiswahili and reads naturally.
- [ ] **Run the same claim again** shows the identical-hash message.
- [ ] The audit seal says "Chain verified" and the entry count goes up with each check.

## Batch check

- [ ] **Download template** gives a CSV that uploads without errors.
- [ ] `data/synthetic/claims.csv` uploads, shows progress, then a result with 44 claims.
- [ ] A file that is not a CSV, an empty file, a file over 2 MB and a file with unknown columns each give a clear message.
- [ ] A row with a bad amount is reported by row number, and the other rows still run.
- [ ] The verdict filter and paging work, and a row opens its full trace.

## History and Overview

- [ ] Sorting by each column works, and paging shows the right total.
- [ ] A history row opens the stored trace with its sources.
- [ ] Overview shows revenue protected, revenue at risk and the chart. The 7, 30 and 90 day ranges change the numbers.
- [ ] A clerk account does not see Overview.

## Device and browser

- [ ] Phone width (390 px): the bottom navigation works, nothing scrolls sideways, the form is usable.
- [ ] Chrome, Firefox and Safari (including iPhone) look the same.
- [ ] Dark mode (system setting) is readable.
- [ ] Keyboard only: Tab reaches every control, drawers close with Escape.

## Security spot checks

- [ ] Paste `<script>alert(1)</script>` into the claim reference. The form refuses it.
- [ ] After signing out, opening `/claims` sends you to sign in.
- [ ] Nothing in the browser storage (Application tab) holds a token or a patient identifier.
