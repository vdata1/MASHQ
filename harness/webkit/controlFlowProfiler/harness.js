var $vm = {
  hasBasicBlockExecuted: function (func, expr) {
    return expr === "return 20";
  },
};

if ($vm.hasBasicBlockExecuted) {
  console.log("The basic block has already executed!");
} else {
  console.log("The basic block has not been executed yet.");
}

var hasBasicBlockExecuted = $vm.hasBasicBlockExecuted;

function assert(condition, reason) {
  if (!condition) throw new Error(reason);
}

var ShouldHaveExecuted = true;
var ShouldNotHaveExecuted = false;

function checkBasicBlock(func, expr, expectation) {
  if (expectation === ShouldHaveExecuted)
    assert(hasBasicBlockExecuted(func, expr, "should have executed"));
  else assert(!hasBasicBlockExecuted(func, expr, "should not have executed"));
}
