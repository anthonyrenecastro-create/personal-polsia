# Alchemy Factory — CI `Build programs` diagnosis

- Date: 2026-10-02 (America/Chicago)
- Cycle: Personal Polsia MVP, first cycle — Engineer task, Tier 0/1 only
- Actions taken: read-only API inspection + local source inspection. No files edited, no push, no deploy, no external writes.
- Guardrails respected: MOCK-GOLD strictly devnet; Solana programs remain unverified until CI is green AND a devnet transaction succeeds. This report does not change that status.

## 1. What CI actually failed on (evidence)

### Retrieval method — what I could and couldn't get

- `gh_api.py GET /repos/anthonyrenecastro-create/alchemy-factory/actions/runs/36325451681` — succeeded. Run metadata retrieved.
- `gh_api.py GET /repos/.../actions/runs/36325451681/jobs` — succeeded. Job and step conclusions retrieved.
- `gh_api.py GET /repos/.../actions/runs?per_page=5` — succeeded. Confirmed run 36325451681 (2026-09-27T14:18:47Z) is still the latest run on the repo.
- Job logs via `gh_api.py` itself: NOT available. That helper parses every response as JSON (`gh_api.py` in `~/workspace/skills/github-push/bin/`), and the logs endpoint returns a 302 redirect to a signed plain-text download, not JSON.
- Job logs via the same credential helper, custom script: succeeded. A throwaway script in `/tmp/fetch_logs.py` used `dynamic_credentials.add_surrogate_to_request` (same `custom.github` surrogate as `gh_api.py`, host-restricted to `api.github.com`), requested `/actions/jobs/108637241664/logs` without following redirects, then fetched the signed redirect target with no credential attached. Result: 2,484-line text log (231,541 bytes), saved ephemerally at `/tmp/job_log.txt`. No token or surrogate was written to disk or printed.

### Run / job facts (from the API)

| Item | Value |
| --- | --- |
| Run | 36325451681, `alchemy-factory-ci`, run_number 21, event `push` |
| Created / updated | 2026-09-27T14:18:47Z / 2026-09-27T14:26:17Z |
| head_branch / head_sha | `main` / `23ddcbd4351f2584bfdc364beee366d2de07d2ce` ("Fix temporary borrow in vessel mint validation…") |
| Conclusion | `failure` |
| Job | 108637241664 `build-test`, `failure`, 14:18:49Z → 14:26:16Z |
| Steps 1–8 | all `success` (checkout, setup-node, Install Rust, Install Solana CLI, Install Anchor (avm), Install JS deps, Pin deps for SBF toolchain) |
| Step 9 | `Build programs` — `failure`, 14:22:07Z → 14:26:13Z (`anchor build`, working-directory `programs`) |
| Step 10 | `Anchor tests (local validator)` — `skipped` |

Local applicability: local HEAD is `b758a02c9ac202b3afb8a14163edfa5f91bc3a60` with a clean tree, and `git diff 23ddcbd HEAD` is empty — the local tree is identical to the CI head tree. So the CI log describes exactly the code on disk here.

### The failure inside `anchor build` (from the log, ANSI/timestamps stripped)

`anchor build` compiled crates in this order before dying:

- `alchemy_vault` — Finished release + test profiles
- `alchemy_curve` — Finished release + test profiles
- `alchemy_vessel` — Finished release + test profiles
- `alchemy_factory` — Finished release + test profiles
- `alchemy_dynamic` — FAILED: `error: could not compile 'alchemy_dynamic' (lib) due to 8 previous errors; 16 warnings emitted`, process exit code 1

`alchemy_decay` and `alchemy_proofx` were never reached at the compile stage in this run (their names appear only earlier, in Anchor's program-id sync phase). Their compile status in this run is unknown.

The 8 errors, verbatim (first is the root; the other seven all point at the same struct):

```text
error: the payer specified for an init constraint must be mutable.
   --> programs/alchemy_dynamic/src/lib.rs:289:9
    |
289 |     pub update_record: Account<'info, UpdateRecord>,

error[E0432]: unresolved import `crate`
  --> programs/alchemy_dynamic/src/lib.rs:37:1
   |
37 | #[program]
   | ^^^^^^^^^^ could not find `__client_accounts_ingest_update` in the crate root

error[E0277]: the trait bound `IngestUpdate<'_>: Bumps` is not satisfied   (x4, at lib.rs:125 and lib.rs:37)
error[E0599]: no function or associated item named `try_accounts` found for struct `IngestUpdate` (at lib.rs:37)
error[E0277]: the trait bound `IngestUpdate<'_>: anchor_lang::Accounts<'_, _>` is not satisfied (at lib.rs:37)
```

The 16 warnings are unrelated noise (unexpected `cfg` values `no-entrypoint`/`cpi`/etc. on the `#[program]` macro, one deprecated `realloc` note).

## 2. Root-cause hypothesis, ranked

### #1 — CONFIRMED by the log: `IngestUpdate.update_authority` is the `init` payer but is not declared `mut`

Local file `programs/programs/alchemy_dynamic/src/lib.rs` (note: full local path includes `programs/programs/`; CI's relative path drops the first segment):

- Line 267–269: `#[derive(Accounts)]` / `#[instruction(...)]` / `pub struct IngestUpdate<'info> {`
- Line 270: `pub update_authority: Signer<'info>,` — no `#[account(mut)]`
- Lines 282–289: `update_record` is declared with `init, payer = update_authority, space = UpdateRecord::SPACE, seeds = [...], bump`

Anchor requires an `init` payer account to be mutable (it debits lamports). Because line 270 lacks `mut`, the `Accounts` derive for `IngestUpdate` fails validation at line 289. That single derive failure explains all seven cascading errors: with no generated `Accounts`/`Bumps` impl, the `#[program]` macro at line 37 can't find `__client_accounts_ingest_update` or `try_accounts`, and `Context<IngestUpdate>` at line 125 reports the missing `Bumps`/`Accounts` bounds.

Supporting evidence that `mut` is the intended, house pattern:

- Same file, `InitializeDynamic` lines 251–252: `#[account(mut)] pub authority: Signer<'info>,` pays for its `init` at line 255.
- `alchemy_curve` `Buy` (lib.rs:557–559), `alchemy_proofx` `MintFromAttestation` (324–326), `alchemy_vault` `DepositCollateral`/`PublishProof` (869–870 / 960–961), `alchemy_vessel` `DepositAsset` (601–602): every payer signer in the workspace carries `#[account(mut)]`.
- A workspace-wide scan (all 7 programs) for `payer = <signer>` whose field lacks `mut` returns exactly one hit: `alchemy_dynamic/src/lib.rs:270`. There is no second instance of this bug class waiting in code that already compiled.

### #2 — UNVERIFIED, only reachable after #1 is fixed: `alchemy_decay` / `alchemy_proofx` compile state

They were never compiled in run 36325451681, so nobody has CI evidence for them at this tree. This is not a hypothesis that they are broken — it is an unknown that the next CI run will resolve. No local evidence of the payer/`mut` bug class exists in either program (scan above covers them).

### #3 — RULED OUT for this run: the SBF dependency-pin layer

Earlier failures in this repo's history were edition2024-manifest pins for the Solana platform-tools cargo. Not this run: step 8 (`Pin deps for SBF toolchain`) succeeded, and the dynamic failure is a source-level Anchor constraint error, not a resolution error. The workflow pin comments (`.github/workflows/ci.yml`) remain relevant background for future runs, but they are not implicated here.

## 3. Exact files / lines implicated

| File | Lines | Problem |
| --- | --- | --- |
| `programs/programs/alchemy_dynamic/src/lib.rs` | 270 | `pub update_authority: Signer<'info>,` — missing `#[account(mut)]` while serving as `init` payer |
| `programs/programs/alchemy_dynamic/src/lib.rs` | 282–289 | `update_record` `init, payer = update_authority, …` — the constraint Anchor rejects (CI error location 289:9 matches this line locally) |
| `programs/programs/alchemy_dynamic/src/lib.rs` | 37, 125 | Cascade-only: `#[program]` macro and `Context<IngestUpdate>` report the missing generated impls; no independent defect here |
| `.github/workflows/ci.yml` | step `Build programs` | Correctly surfaces the failure (`anchor build` in `programs/`); no workflow change needed for this fix |

No other file is implicated by the evidence.

## 4. Smallest next fix to try

One line, in `programs/programs/alchemy_dynamic/src/lib.rs`, matching `InitializeDynamic` (line 251) and every other payer in the workspace:

```diff
 pub struct IngestUpdate<'info> {
+    #[account(mut)]
     pub update_authority: Signer<'info>,
```

Why I did NOT apply it in this task: the fix is trivial and local-only, but this VM has no Rust/Anchor toolchain (`cargo`/`anchor`/`rustc` not present), so I cannot verify it locally — and the task rules say prefer a precise diagnosis over an unverifiable edit. Applying it is a Tier-1 code change for Zebulon's approval, followed by a push (Tier 2, separate approval) to let CI verify.

Expected verification after the fix is pushed: step 9 `Build programs` compiles `alchemy_dynamic`, then compiles `alchemy_decay` and `alchemy_proofx` for the first time at this tree — that is the next evidence to read before claiming anything further. Even a green `anchor build` leaves the programs unverified overall: CI green + a successful devnet transaction is still the bar, and step 10 (`anchor test`, local validator) was skipped in this run and has not yet been observed passing.

## 5. What was not checked

- No local build was attempted or is possible on this VM (no toolchain).
- `alchemy_decay` / `alchemy_proofx` compile and test status at this tree: unknown.
- `anchor test` (step 10) behavior: never observed at this tree; it was skipped.
- Anything about devnet deployment or transactions: out of scope for this Tier 0/1 task, and per guardrails would require separate approval.
