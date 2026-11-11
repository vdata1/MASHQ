let x = require("assert")

var MjsUnitAssertionError = class MjsUnitAssertionError {
  constructor(message_func) {
    let prevPrepareStackTrace = Error.prepareStackTrace;
    try {
      Error.prepareStackTrace = MjsUnitAssertionError.prepareStackTrace;
      this.stack = new Error("MjsUnitAssertionError").stack;
    } finally {}
  }
}
 
// Monkey-patchable all-purpose failure handler.
var failWithMessage;
var ArrayPrototypePush = Array.prototype.push;
MjsUnitAssertionError.prepareStackTrace = function(error, stack) {
      for (let i = 0; i < stack.length; i++) {
        let frame = stack[i];
        let file = frame.getFileName();
        }
  }
failWithMessage = function failWithMessage(message) {
    throw new MjsUnitAssertionError(()=>message);
  }
Object.defineProperty(Array.prototype, "0", {
  get: failWithMessage,
  set: failWithMessage
});
var ones = eval("[" + Array(12 * 1024).join("1,") + 1 + "]");
