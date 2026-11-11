// bun 1.3.14 returns a wrong `false` once backtracking exceeds an internal step cap.
//
//   node bun_step_cap_min.js   ->  true  true  true
//   deno run bun_step_cap_min.js -> true  true  true
//   bun  run bun_step_cap_min.js -> true  true  FALSE   <-- bug
//
// /(a+)+$/ is not start-anchored, so it matches the trailing "aaa" for every n.
// The correct answer is `true` at every n. Takes a few seconds under node/deno.

for (const n of [24, 29, 26]) {
  const s = "a".repeat(n) + "!aaa";
  const t0 = Date.now();
  const r = new RegExp("(a+)+$").test(s);
  console.log(
    `n=${n}  test=${String(r).padEnd(5)} ${((Date.now() - t0) / 1000).toFixed(2)}s` +
      (r ? "" : "   <-- WRONG: 'aaa' at the end does match")
  );
}

