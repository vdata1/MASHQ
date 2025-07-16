//function-code_10.4.3-1-71-s_transfer_port.js

function f() {
  "use strict";
  console.log(this);

  return this === undefined;
}
console.log(f());

