let rab = new ArrayBuffer(1, { maxByteLength: 2});
let ta = new Int8Array(rab);

let value = {
  valueOf() {
    rab.resize(2);
    return 123;
  },
};

ta.fill(value);
ta.fill(value);
console.log(ta)
console.log(ta[0]);
console.log(ta[1]); //bun: 0, node&deno: 123
console.log(ta.length)
