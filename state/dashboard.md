# Personal Polsia — Dashboard

Updated: 2026-10-02 (first cycle, manual run)
Operator: Evie (Muse) for Zebulon

## Decision needed first

**Quadra production send-for-review.** Draft release is staged (US only,
bundle v2 / 1.0.0). Nothing submitted. Public release notes are drafted
and waiting for your approval — see
`briefings/quadra-production-release-notes-draft.md`. The send, if you
approve it, also bundles the older Alpha/Team Apex tester-list change
under "Submit 2 changes."

## Company pulse (verified 2026-10-02 via scripts/check_status.py)

| Company | Live / CI check | Next milestone | Biggest open loop |
|---|---|---|---|
| Quadra-M.I.N.D. Sight | Live site HTTP 200; local master HEAD 8e8454a, 13 dirty local paths (Android/TWA files, expected) | Send production release for review after notes approval | Release notes rewrite (drafted, awaiting approval); keystore off-VM backup not done; GEMINI_API_KEY not on Render |
| Alchemy Factory | Billing fixed by Zebulon 2026-10-02; CI run 37071541814 executed on main 36d49cc. 5 programs compiled incl. alchemy_dynamic (payer-mut fix works); Build programs failed at alchemy_proofx (2x E0308 COption vs Option at lib.rs:139,207); decay still never compiled; anchor test skipped | CI green after proofx .into() fix (awaiting approval to apply+push), then devnet deploy with separate approval | proofx COption fix identified, not applied; decay compile + anchor test still unknown; programs UNVERIFIED |
| newsletter-autopilot | Local project present, not a git repo on VM; no CI runs; GitHub is source of truth | Live Shopify connection check | Token not yet captured/tested via Secure Vault; 5 product decisions open (draft source, AI provider, surface, review gate, scheduler) |

## System state

- Registry: 3 companies (`companies/*.yaml`)
- Agents: CEO, Validator, Engineer, Growth, Comms, Ops (`agents/*.md`)
- Cron: nightly CEO cycle + morning briefing — wiring this cycle
- Cost: $0 new subscriptions; uses existing Muse/GitHub/Render

## Guardrails in force

Tier 2 (needs Zebulon every time): pushes to main, deploys, Play submissions,
sending email/messages, public posts, ad spend, payments, on-chain deploys.
No task is "done" without a check (HTTP, CI, GitHub API, file, screenshot).
