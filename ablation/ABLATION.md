# MASHQ ablation runbook (USENIX '27 revision)

Prepared for Abdullah to run. Answers the ablation asks from reviewers B, C, and D:
which mutation operators and which oracle actually drive the bug findings.

## What was changed in the code

Only one place: the operator selector in `fuzz/testFuzz/fuzzer_multi_proc.js`
(`chooseAndMarkModification`). It now reads the operator set and weights from two
environment variables, falling back to the paper's exact configuration when they
are unset. Nothing else in the fuzzer changed, and with no env vars set the
behavior is identical to the submitted version.

- `MASHQ_OPS` — comma-separated subset of `delete,inject_snippet,transfer`
- `MASHQ_WEIGHTS` — optional, comma-separated, same order as `MASHQ_OPS`.
  If omitted, each operator keeps its paper weight and `weightedRandom`
  renormalizes over whatever subset is active.

Operator meanings (confirm the third before trusting cell A1):
- `delete` — delete a random AST subtree. No snippet.
- `inject_snippet` — inject one of the 12 runtime-specific API tuples
  (`translation/`). This is the "runtime-specific API injection" reviewers name.
- `transfer` — recombine AST fragments from another seed test. **Caveat:** the
  `mergeAST` / `snippetAST` wiring in `markLocation.js` is partly commented out.
  Please confirm `transfer` pulls from the other seed test and not from the
  runtime-specific snippet before reporting A1 as "no API injection."

## 2-minute sanity check before the budgeted run

In your working environment (deps installed, corpus present), confirm the lever
works before spending machine time. Generate a few rounds on a small seed slice
with and without injection, then check the modification comments in the output:

```bash
cd fuzz/testFuzz
MASHQ_OPS="delete,transfer" node --expose-gc main_multi_process.js   # no injection
# inspect generated files; none should say inject_snippet / inject_beggining / inject_end:
grep -rhoE "Modification: [a-z_]+" output/ | sort | uniq -c
```

With `MASHQ_OPS="delete,transfer"` the counts should show only `delete` and
`transfer` (and inject variants absent). Unset, all operators appear. The run
also prints `[ablation] operators: [...]` at startup. If injection still appears,
stop — the lever is not wired, ping Alex before burning the budget.

## The matrix

Run each cell under an **equal budget** (same seed corpus, same number of rounds,
same wall-clock or same generated-test count — pick one and hold it fixed across
all cells; state which in the notes). Report per cell: unique confirmed defects
recovered from the paper's 48, unique divergence clusters, and crashes.

| Cell | MASHQ_OPS | Question it answers |
|---|---|---|
| A0 full / baseline | unset (or `delete,inject_snippet,transfer`) | Reproduce the headline under the reduced budget. Reference point. |
| A1 no API injection | `delete,transfer` | D + C: what do mutation + cross-test recombination find with no runtime-specific snippets? |
| A2 inject-only | `inject_snippet` | Isolate the contribution of the 12 tuples. |
| A3 delete/transfer-only | `delete,transfer` | C's "inject vs delete/transfer" — same config as A1, compared against A2. |

A1 and A3 are the same run; report it once and compare against A2 and A0.

Example:

```bash
cd fuzz/testFuzz
# baseline
node --expose-gc main_multi_process.js        # or the usual entry point
# no runtime-specific API injection
MASHQ_OPS="delete,transfer" node --expose-gc main_multi_process.js
# inject-only
MASHQ_OPS="inject_snippet" node --expose-gc main_multi_process.js
```

Set `outputDir` per cell so runs do not overwrite each other.

## The oracle cell (no re-generation needed)

D also asks for cross-runtime differential oracle vs single-runtime crash
detection. This is a **re-analysis of outputs already generated**, not a new
fuzzing run. Over the A0 outputs, count:

- defects a single-runtime watcher catches: a crash or uncaught exception on one
  runtime, ignoring the other two;
- defects that require the cross-runtime diff: all three runtimes return/complete
  but their outputs diverge (the behavioral fingerprints and non-crashing gadgets).

The second set is the part a single-runtime fuzzer structurally cannot find. This
is the number that answers "what does the differential oracle add." The output
comparison lives downstream of `runFuzzOutputs.py`; tag each flagged output as
crash-only or divergence-only and tally.

## What to hand back

A small table (cells A0–A3 plus the oracle split) with the three metrics per
cell, the fixed budget used, and the machine. A directional result is enough for
the 700-word author response; the full-budget version goes in the revision.
