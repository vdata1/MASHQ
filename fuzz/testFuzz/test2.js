var assert = require('assert');

assert.sameValue = function (actual, expected, message) {
    try {
      if (actual == expected) {
        console.log("Dang")
        return;
      } else{
        console.log("dude")
      }
    } catch (error) {
      console.log("somehting")
      return;
    }  
  };
// Round: 10, Runtime: node, Test: ../../../test262/test/language/identifier-resolution/S10.2.2_A1_T1.js, Snippet: getHOME, additionalTestAST: ../../../test262/test/built-ins/DataView/prototype/getInt16/negative-byteoffset-throws.js, Modification: delete
var {spawn} = require('child_process');

var x = 0;
function f1() {
  var x = 1;
  Array.prototype[Symbol.iterator] = function* () {
    if (this.length > 2) {
      yield 42;
    }
  };
  var iterCount = 0;
  for (let [x, y, z] = [1, 2, 3]; iterCount < 1;){
    assert.sameValue(z, 42);
    iterCount += 1;
  }
  
  function f2() {
    var {spawn} = require('child_process');
    (async function () {
      var proc = spawn("node", ["--version"]);
      console.log("subprocess forked");
      proc.kill('SIGTERM');
      console.log("killing subprocess")
      await new Promise(function (resolve) {
        console.log("killing subprocess")
        proc.on('exit', resolve);
      });
      console.log("subprocess killed");
    })();
    return x;
  }
  ;
  return f2();
}
f1();