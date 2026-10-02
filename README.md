# Personal Polsia — Zebulon's Night Shift

A single-user, self-owned version of Polsia. No subscription, no revenue
share, no credit burn, no lock-in.

Polsia's model: specialized agents run a company on daily cycles while the
founder sleeps, then deliver a morning briefing. This system does the same
loop on infrastructure Zebulon already owns and controls:

- Code lives in his GitHub (`anthonyrenecastro-create`)
- Apps deploy to his Render / Play accounts
- Commerce runs through his Shopify / Stripe (when he enables it)
- The operator is Evie (Muse) + subagents, crons, and his connected skills

## Companies under management (v1)

| Company | What it is | Stage |
|---|---|---|
| Quadra-M.I.N.D. Sight | Metacognitive training PWA → Play Store | Production draft staged, awaiting send-for-review decision |
| Alchemy Factory | Solana creator studio for experimental tokens | Stage 4 security fixes in, CI red since 2026-09-27, devnet deploy not approved |
| newsletter-autopilot | Shopify free-tier newsletter automation | Publish step built, Shopify token not yet captured/tested |

See `companies/*.yaml` for the registry.

## How a cycle works

1. **Nightly CEO pass** (cron, ~23:00 America/Chicago): read this registry,
   each company's `STATE.md` notes, goals, memory, live checks
   (`scripts/check_status.py`), and recent activity.
2. **Plan:** pick at most 3 tasks per company, ranked by the company's
   `next_milestone`. Every task gets an owner agent, an autonomy tier, and a
   proof-of-done check *before* work starts.
3. **Execute Tier 0/1 only overnight:** research, drafting, local code,
   tests, status checks. Nothing external ships while he sleeps.
4. **Queue Tier 2 for approval:** deploys, pushes to main, emails, posts,
   ad spend, submissions, payments. These arrive as prepared work with a
   one-tap decision.
5. **Morning briefing** (~07:00): what was verified done, what is waiting
   on him, what is blocked, and the single most important decision of the day.
   No task is marked done without evidence linked in the briefing.

## The three enhancements over Polsia

1. **Validation gate before build/spend.** No new company, feature, or
   campaign starts until `templates/validation-gate.md` is answered with
   sourced demand evidence. Polsia builds first and asks never; we ask first.
2. **Proof-of-done.** "Complete" requires a check: HTTP 200, CI green,
   GitHub API confirms the ref, a screenshot, a transaction, a test run.
   Failed work is reported as failed — never charged, never hidden.
3. **Autonomy tiers with a human brake.** See `OPERATING_SYSTEM.md`.
   Outbound commitments (email to real people, ads, public posts, store
   submissions) never happen without Zebulon's explicit approval.

## Files

- `OPERATING_SYSTEM.md` — architecture, agent roster, tiers, guardrails
- `companies/` — one YAML per company (vision, milestone, metrics, channels, guardrails)
- `agents/` — role prompts (CEO, Validator, Engineer, Growth, Comms, Ops)
- `templates/` — morning briefing, task card, validation gate
- `scripts/check_status.py` — deterministic live/local checks, JSON out
- `briefings/` — dated morning briefings (`YYYY-MM-DD.md`)
- `cycles/` — dated nightly cycle logs
- `state/dashboard.md` — current one-page state, regenerated each cycle

## Cost

$0 in new subscriptions. Marginal cost is the Muse usage and infra
Zebulon already pays for (Render free tier, GitHub, his model access).
Compare: Polsia at $20–$1,000/mo + 3% of revenue + 20% of ad spend,
on their infrastructure, with withdrawal caps.

## Status

MVP built 2026-10-02. First cycle run manually the same day.
Nightly cron: `personal-polsia-ceo-cycle`. Morning delivery is the
cron's chat report in the originating chat unless Zebulon redirects it.
