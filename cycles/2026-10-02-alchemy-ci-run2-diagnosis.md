# Alchemy Factory — CI `Build programs` diagnosis, run 2 (37071541814)

- Date: 2026-10-02 (America/Chicago)
- Cycle: Personal Polsia MVP, first cycle — Engineer task, Tier 0/1 only, read-only follow-up
- Actions taken: read-only API inspection + log fetch + local source inspection. **No files edited, no push, no deploy, no external writes.**
- Guardrails respected: MOCK-GOLD strictly devnet; Solana programs remain **UNVERIFIED** until CI is green AND a devnet transaction succeeds. This report does not change that status. Devnet deploy still requires Zebulon's separate explicit approval.

## 1. What CI actually did this time (evidence)

### Retrieval method

Same method as the run-1 diagnosis (`2026-10-02-alchemy-ci-diagnosis.md`):
- `gh_api.py GET /repos/anthonyrenecastro-create/alchemy-factory/actions/runs/37071541814` — succeeded.
- `gh_api.py GET /repos/.../actions/runs/37071541814/jobs` — succeeded.
- Job log via throwaway script `/tmp/fetch_logs2.py` using `dynamic_credentials.add_surrogate_to_request` (credential `custom.github`, host `api.github.com` only), no-redirect handling, then unauthenticated fetch of the signed redirect target. Result: 2,576-line text log (243,105 bytes) saved ephemerally at `/tmp/job_log2.txt`; cleaned (ANSI + timestamps stripped) copy at `/tmp/job_log2_clean.txt`. No token or surrogate was written to disk, printed, or logged.

### Run / job facts (from the API)

| Item | Value |
| --- | --- |
| Run | 37071541814, `alchemy-factory-ci`, run_number 23, event `workflow_dispatch` |
| Created / updated | 2026-10-02T22:15:56Z / 2026-10-02T22:27:07Z |
| head_branch / head_sha | `main` / `36d49cc32735344c2517c82c3ac3fc1ef1824537` ("Fix IngestUpdate: mark update_authority mut (init payer must be mutable)") |
| Conclusion | `failure` |
| Job | 111051894896 `build-test`, `failure`, 22:16:01Z → 22:27:06Z |
| Steps 1–8 | all `success` (Set up job, checkout, setup-node, Install Rust, Install Solana CLI, Install Anchor (avm), Install JS deps, Pin deps for SBF toolchain) |
| Step 9 | `Build programs` — `failure`, 22:20:09Z → 22:27:03Z (`anchor build`, working-directory `programs`) |
| Step 10 | `Anchor tests (local validator)` — `skipped` |

Billing note: unlike runs 37021349317 / 37021442323 (both `startup_failure`, 0 jobs, GitHub account billing block on `anthonyrenecastro-create`), this run actually started and executed all steps after Zebulon paid the account. The failure is now a genuine code compile failure, not a billing/startup failure.

### Local applicability

- Local HEAD: `7f28c47` on `main` (clean tree in prior checks; this diagnosis made no edits). `git diff 23ddcbd HEAD --stat` = exactly 1 file changed, 4 insertions — the `alchemy_dynamic` payer-mut fix. That is the local cherry-pick equivalent of GitHub commit `36d49cc` (single-file commit on top of `23ddcbd`).
- Remote-vs-local file identity verified via the contents API at ref `36d49cc`:
  - `programs/programs/alchemy_proofx/src/lib.rs` — GitHub blob `a0620797248125eab46cc8d6f4c20ec74c9602b2`, SHA-256 `c23006c90db8c307a40d3032adbb8e5563fa5e1d16f8e27e96742f90ab1b036a`, identical to local file (same git hash-object).
  - `programs/programs/alchemy_dynamic/src/lib.rs` — GitHub blob `fe6aaf8ddd8aff2336e85500e373a04865770109`, SHA-256 `5c276727d950400a8e40975e2eba080935fbc824613eba5731d79e721767713b`, identical to local file, and it contains the fix at `IngestUpdate`: comment + `#[account(mut)] pub update_authority: Signer<'info>,` (local lines 270–273).
  - `programs/programs/alchemy_decay/src/lib.rs` — GitHub blob `63bb0878b5b668d8ddaad00d153f9632d2aa795d`, SHA-256 `b186265a72bddf12aa959b63f416b04afe340036cb0c86b37e5077543f6ad1ba`, identical to local file.
- So the CI log describes exactly the code on disk here. CI paths drop the first `programs/` segment (`programs/alchemy_proofx/src/lib.rs` in the log = `programs/programs/alchemy_proofx/src/lib.rs` locally).

## 2. Did `alchemy_dynamic` compile this time? Yes.

Compile order and outcome inside `anchor build` (log lines from the cleaned log):

| Order | Program | Result |
| --- | --- | --- |
| 1 | `alchemy_vault` | Finished `release` (2m 29s) + Finished `test` (1m 12s) |
| 2 | `alchemy_curve` | Finished `release` + Finished `test` |
| 3 | `alchemy_vessel` | Finished `release` + Finished `test` |
| 4 | `alchemy_factory` | Finished `release` (16.72s) + Finished `test` (7.24s) |
| 5 | `alchemy_dynamic` | **Finished `release` (2.76s) + Finished `test` (1.33s)** — log lines 2247, 2380–2382 |
| 6 | `alchemy_proofx` | **FAILED** — log line 2384 onward; `error: could not compile 'alchemy_proofx' (lib) due to 2 previous errors; 18 warnings emitted`, process exit code 1 |
| 7 | `alchemy_decay` | **Never reached** — its name appears only in Anchor's earlier program-id sync phase (log lines 909–912), not at the compile stage. Compile status at this tree still **unknown**. |

The payer-mut fix pushed as `36d49cc` therefore works: the exact struct that failed in run 36325451681 now compiles in both profiles. The build advanced one program further and exposed the next latent failure, in `alchemy_proofx`, which had never been compiled at this tree before (in run 1 the build died at `alchemy_dynamic` first).

## 3. The new failure, verbatim

Both errors are the same type mismatch, in `alchemy_proofx`, at the two places that validate mint authority (ANSI/timestamps stripped):

```text
error[E0308]: mismatched types
--> programs/alchemy_proofx/src/lib.rs:139:49
|
139 |             ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key()),
|             --------------------------------    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ expected `COption<Pubkey>`, found `Option<Pubkey>`
|             |
|             expected because this is `COption<__Pubkey>`
|
= note: expected enum `COption<__Pubkey>`
found enum `Option<__Pubkey>`
help: call `Into::into` on this expression to convert `Option<__Pubkey>` into `COption<__Pubkey>`
|
139 |             ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key()).into(),
|                                                                                        +++++++

error[E0308]: mismatched types
--> programs/alchemy_proofx/src/lib.rs:207:49
|
207 |             ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key()),
|             --------------------------------    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ expected `COption<Pubkey>`, found `Option<Pubkey>`
|             |
|             expected because this is `COption<__Pubkey>`
|
= note: expected enum `COption<__Pubkey>`
found enum `Option<__Pubkey>`
help: call `Into::into` on this expression to convert `Option<__Pubkey>` into `COption<__Pubkey>`
|
207 |             ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key()).into(),
|                                                                                       +++++++
```

Summary line: `error: could not compile 'alchemy_proofx' (lib) due to 2 previous errors; 18 warnings emitted`. The 18 warnings are the same class of noise as run 1 (unexpected `cfg` values `no-entrypoint`/`cpi`/`custom-heap`/etc. on the `#[program]` macro at lib.rs:68, plus one deprecated `realloc` note) — not implicated in the failure.

### Local source at the implicated lines

File `programs/programs/alchemy_proofx/src/lib.rs`:
- Line 139, in `initialize_proofx` (anti-squatting check: only the mint's current mint authority may publish the config):
  ```rust
  ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key()),
  ```
- Line 207, in `mint_from_attestation` (the proofx-config PDA must be the mint authority):
  ```rust
  ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key()),
  ```
- The `mint` account in both instructions is `InterfaceAccount<'info, Mint>` (`anchor_spl::token_interface::Mint`, imported at line 64; account declarations at lines ~313 and ~332). For the Token-2022 / token-interface `Mint` type, the `mint_authority` field is SPL Token's `COption<Pubkey>`, **not** Rust's standard `Option<Pubkey>`. The code compares it against `Some(...)`, which is a standard `Option`, hence E0308 at both sites.

## 4. Classification

- **Not the payer-mut bug class.** Workspace re-scan for this run: every `payer = <signer>` field across all 7 programs now carries `#[account(mut)]` (curve, decay, dynamic incl. the fixed `update_authority`, factory, proofx, vault, vessel — no misses). There is no second payer-mut instance waiting.
- **Not a toolchain / SBF-pin issue.** Steps 1–8 all succeeded (including `Pin deps for SBF toolchain`), and five programs — including the previously failing `alchemy_dynamic` — compiled in both release and test profiles. The failure is a source-level type error.
- **Not the same comparison bug elsewhere.** Workspace scan for `== Some(` and for `mint_authority`/`freeze_authority` comparisons: the only two hits in the entire workspace are proofx lines 139 and 207. No `COption` handling exists anywhere else in the programs today.
- **Yes: a first-compile latent bug in `alchemy_proofx`.** This is proofx's first-ever compile at this tree (run 1 died at dynamic before reaching it). The bug was presumably present since proofx was written; it was masked, not introduced, by the dynamic failure. The two error sites are independent instances of the same one-line pattern (validate mint authority by equality), so both must be fixed for proofx to compile — fixing only line 139 would still leave line 207 failing.

## 5. Root cause, ranked

### #1 — CONFIRMED by the log: `COption<Pubkey>` vs `Option<Pubkey>` mismatch at proofx lines 139 and 207

`InterfaceAccount<Mint>::mint_authority` is `COption<Pubkey>` (SPL Token's C-compatible option type). Both validation checks construct a standard-library `Some(Pubkey)` and compare with `==`. Rust's type checker rejects `COption<Pubkey> == Option<Pubkey>` (E0308). That's the whole failure: 2 errors, both at the comparison, nothing else in proofx is implicated by this log.

### #2 — STILL UNKNOWN, only reachable after #1 is fixed: `alchemy_decay` compile state

Decay was again never compiled (build died at proofx, which Anchor builds before decay in this workspace's order). There is no local evidence of either bug class in decay (payer-mut scan covers it; no `== Some(` / mint-authority comparisons in it), but "no evidence of these two bug classes" is not "compiles" — its status at this tree remains unknown until a CI run reaches it.

### #3 — RULED OUT for this run: billing/startup and dependency-pin layers

Billing was paid and the run executed fully (contrast `startup_failure` runs 37021349317 / 37021442323). Pin step succeeded; five programs compiled. Neither layer is implicated.

## 6. Exact files / lines implicated

| File | Lines | Problem |
| --- | --- | --- |
| `programs/programs/alchemy_proofx/src/lib.rs` | 139 | `ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key())` — `Option<Pubkey>` compared against `COption<Pubkey>` (E0308) |
| `programs/programs/alchemy_proofx/src/lib.rs` | 207 | `ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key())` — same E0308 |
| `programs/programs/alchemy_proofx/src/lib.rs` | 64, ~313, ~332 | Context only: `Mint` is the token-interface type whose `mint_authority` is `COption<Pubkey>`; the account declarations themselves are not defective |
| `programs/programs/alchemy_dynamic/src/lib.rs` | 270–273 | **Fixed and now verified compiling** — `#[account(mut)]` on `IngestUpdate.update_authority` (commit `36d49cc`) |
| `.github/workflows/ci.yml` | step `Build programs` | Correctly surfaces the failure (`anchor build` in `programs/`); no workflow change needed for this fix |

No other file is implicated by the evidence.

## 7. Smallest next fix to try (NOT applied in this task)

Two one-token changes in `programs/programs/alchemy_proofx/src/lib.rs`, exactly as the compiler suggests — convert the standard `Option` into `COption` at each comparison:

```diff
-            ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key()),
+            ctx.accounts.mint.mint_authority == Some(ctx.accounts.mint_authority.key()).into(),
```

```diff
-            ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key()),
+            ctx.accounts.mint.mint_authority == Some(ctx.accounts.proofx_config.key()).into(),
```

Why this shape: it changes nothing about *what* is being checked (the mint's mint authority must equal, respectively, the signing mint authority at config creation, and the proofx-config PDA at mint time) — it only converts the constructed value to the `COption<Pubkey>` type the field actually has, which is the conversion `rustc` itself proposes. Semantics of both security checks are preserved.

Not applied here because: (a) this task is read-only diagnosis (Tier 0/1, no edits), and (b) this VM has no Rust/Anchor toolchain, so the fix cannot be verified locally — CI is the verifier. Applying it would be a Tier-1 code change for Zebulon's approval, followed by a push (Tier 2, separate approval).

Expected verification after the fix is pushed: `Build programs` should compile `alchemy_proofx`, then compile `alchemy_decay` for the first time at this tree — that is the next evidence to read. Even a fully green `anchor build` would **not** by itself verify the programs.

## 8. What remains unknown / not checked

- `alchemy_decay` compile and test status at this tree: unknown (never reached in either run).
- `anchor test` (step 10, local validator): skipped again; has never been observed running, let alone passing, at this tree.
- No local build was attempted or is possible on this VM (no toolchain).
- Devnet deployment / any devnet transaction: not attempted, out of scope, and requires Zebulon's separate explicit approval. Programs remain **UNVERIFIED** — the standing bar is CI green **plus** a successful end-to-end devnet transaction.
- Whether there are further latent errors inside proofx *after* these two comparisons (e.g. borrow or trait issues the compiler hasn't reached yet): possible in principle — rustc stops at these errors — but there is no evidence of any in this log; the next CI run is the check.
