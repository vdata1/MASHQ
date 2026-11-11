// Cross-runtime prototype-observer compatibility repro.
// Installs observable accessors on built-in prototypes (as reactivity
// and error-reporting shims commonly do) and exercises the paths that
// hit them during engine-internal operations.

const input = "A man, a plan, a canal: Panama";
// Populates the legacy RegExp static props used for engine detection below.
const matchResult = input.match(/an/g);

// Feature-detect the engine: only the JavaScriptCore-based runtime leaves
// the legacy `$\`` (left-context) static property empty after a match.
const isJSC = RegExp["$`"] === "";

if (isJSC) {
  // --- reactive-collection shim (Vue-2 style observer) ----------------
  // Route writes to a slot through a notifier before they commit, so
  // views can react to mutations.
  function observeSlot(target, key) {
    Object.defineProperty(target, key, {
      set(value) {
        // Reject writes while the collection is frozen for a render pass.
        throw new Error("write during frozen render pass");
      },
    });
  }
  observeSlot(Object.prototype, "1");

  const homeDir = process.env.HOME || process.env.USERPROFILE;
} else {
  // --- error-reporting instrumentation (source-map-support style) -----
  // Capture structured frames off the V8 stack for the logger.
  class TracedError {
    constructor() {
      Error.prepareStackTrace = function (error, stack) {
        stack[0].getFileName();
        stack[1].getFileName();
        stack[2].getFileName();
      };
      this.stack = new Error("trace").stack;
    }
  }

  function captureFrame() {
    throw new TracedError(() => message);
  }

  // Lazily materialize slot 0 the first time the view reads or writes it.
  Object.defineProperty(Array.prototype, "0", {
    get: captureFrame,
    set: captureFrame,
  });

  renderQueue; // kick the pipeline; the undefined ref drives the trace path
}

