# Clinic interview guide

Goal: learn what SHA rejections really cost facilities, what billing staff do today to avoid them, and what they would pay for a pre-check. Aim for 3 to 5 interviews of 20 to 30 minutes with billing clerks, facility managers or finance staff at facilities of different levels (Level 2 to 5, private, mission and county).

## Before the call

- Say who you are and what Hakiki is in two sentences: "It checks an SHA claim before you submit it, tells you which rule it would fail, cites the regulation, and shows the smallest fix."
- Ask permission, and write down the answer: "May I take notes? May I quote you, without naming you or the facility? You can stop at any time."
- Do not ask for patient information or claim details that identify a person.

## Questions

1. Walk me through what happens from the moment a patient is treated to the day SHA pays.
2. Which claims get rejected or delayed most often? What are the top three reasons you see?
3. When a claim is rejected, how do you find out why? How long does that take?
4. Roughly how many claims do you submit a month? What share are rejected or delayed?
5. What is an average rejected claim worth, in KES? How much money is stuck right now?
6. What does a rejection cost besides the money: staff time, re-submissions, cash-flow problems?
7. What do you check before you submit a claim today? Who does it, and with what tools?
8. Pre-authorisation: which services need it, how long does it take, and what goes wrong?
9. Referrals: how do you record the referral reference for services that need one?
10. What would make you trust an automatic pre-check? What would make you stop using it?
11. Would you pay for it? How would you prefer to pay: per claim, a monthly fee, or a share of the money recovered? What would be too expensive?
12. Are you comfortable sending claim data to a tool if patient identifiers are hashed first? Who would have to approve that?
13. Who else should I talk to?

## Notes template (`docs/interviews.md`)

Keep one block per interview. Anonymise the facility ("Level 4 mission hospital, Nairobi").

```
### Interview N · date · role · facility type and level
- Claims per month / share rejected:
- Top rejection reasons (their words):
- Average value of a rejected claim (KES):
- What they check today, and who:
- Pre-authorisation and referral pain:
- Would pay? How much, and how:
- Data and approval concerns:
- Quote (permission given: yes / no):
```

## After the interviews

Write a summary at the top of `docs/interviews.md`: the three biggest pains, the average KES lost per rejection, the price signals, and one or two quotes you may use in the pitch.

## Second visit: show the app (15 minutes)

1. Open the live demo and check the sample claim. Ask: "Is this the reason you would expect this claim to be rejected?"
2. Open the source drawer on a rule. Ask: "Does this match how you understand the regulation?"
3. Apply the fix. Ask: "Would your staff trust this, and what would they still check by hand?"
4. Show the Overview. Ask: "Which of these numbers would you look at every week?"
5. Ask for one sentence about the tool that you may quote.
