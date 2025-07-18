/*
 * Copyright (C) 2016-2017 Apple Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL APPLE INC. OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

//import { description } from "./WebKit-main/JSTests/wasm/WASM.js";

const assert = {
  _fail: (msg, extra) => {
    throw new Error(msg + (extra ? ": " + extra : ""));
  },

  isNotA: (v, t, msg) => {
    if (typeof v === t) assert._fail(`Shouldn't be ${t}`, msg);
  },

  isA: (v, t, msg) => {
    if (typeof v !== t) assert._fail(`Should be ${t}, got ${typeof v}`, msg);
  },

  isNotUndef: (v, msg) => assert.isNotA(v, "undefined", msg),
  isUndef: (v, msg) => assert.isA(v, "undefined", msg),
  notObject: (v, msg) => assert.isNotA(v, "object", msg),
  isObject: (v, msg) => assert.isA(v, "object", msg),
  notString: (v, msg) => assert.isNotA(v, "string", msg),
  isString: (v, msg) => assert.isA(v, "string", msg),
  notNumber: (v, msg) => assert.isNotA(v, "number", msg),
  isNumber: (v, msg) => assert.isA(v, "number", msg),
  notFunction: (v, msg) => assert.isNotA(v, "function", msg),
  isFunction: (v, msg) => assert.isA(v, "function", msg),

  hasObjectProperty: (o, p, msg) => {
    assert.isObject(o, msg);
    assert.isNotUndef(o[p], msg, `expected object to have property ${p}`);
  },

  isArray: (v, msg) => {
    if (!Array.isArray(v))
      assert._fail(`Expected an array, got ${typeof v}`, msg);
  },

  isNotArray: (v, msg) => {
    if (Array.isArray(v)) assert._fail(`Expected to not be an array`, msg);
  },

  truthy: (v, msg) => {
    if (!v) assert._fail(`Expected truthy`, msg);
  },

  falsy: (v, msg) => {
    if (v) assert._fail(`Expected falsy`, msg);
  },

  eq: (lhs, rhs, msg) => {
    if (typeof lhs !== typeof rhs)
      assert._fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
    if (Array.isArray(lhs) && Array.isArray(rhs) && lhs.length === rhs.length) {
      for (let i = 0; i !== lhs.length; ++i) assert.eq(lhs[i], rhs[i], msg);
    } else if (lhs !== rhs) {
      if (typeof lhs === "number" && isNaN(lhs) && isNaN(rhs)) return;
      assert._fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
    } else {
      if (typeof lhs === "number" && 1.0 / lhs !== 1.0 / rhs)
        assert._fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
    }
  },

  matches: (lhs, rhs, msg) => {
    if (typeof lhs !== "string" || !(rhs instanceof RegExp))
      assert._fail(
        `Expected string and regex object, got ${typeof lhs} and ${typeof rhs}`,
        msg
      );
    if (!rhs.test(lhs)) assert._fail(`"${msg}" does not match ${rhs}`, msg);
  },

  canonicalizeI32: (number) => {
    if (Math.round(number) === number && number >= 2 ** 31)
      number = number - 2 ** 32;
    return number;
  },

  eqI32: (lhs, rhs, msg) => {
    return assert.eq(
      assert.canonicalizeI32(lhs),
      assert.canonicalizeI32(rhs),
      msg
    );
  },

  ge: (lhs, rhs, msg) => {
    assert.isNotUndef(lhs);
    assert.isNotUndef(rhs);
    if (!(lhs >= rhs)) assert._fail(`Expected: "${lhs}" < "${rhs}"`, msg);
  },

  le: (lhs, rhs, msg) => {
    assert.isNotUndef(lhs);
    assert.isNotUndef(rhs);
    if (!(lhs <= rhs)) assert._fail(`Expected: "${lhs}" > "${rhs}"`, msg);
  },

  _throws: (func, type, message, ...args) => {
    try {
      func(...args);
    } catch (e) {
      if (
        e instanceof type &&
        (typeof e.message == "undefined" || e.message.indexOf(message) >= 0)
      )
        return e;
      assert._fail(
        `Expected to throw a ${type.name} with message "${message}", got ${e.name} with message "${e.message}"`
      );
    }
    assert._fail(`Expected to throw a ${type.name} with message "${message}"`);
  },

  throwsAsync: async (promise, type, message) => {
    try {
      await promise;
    } catch (e) {
      if (e instanceof type) {
        if (e.message === message) return e;
        const evaluatingIndex = e.message.indexOf(" (evaluating '");
        if (evaluatingIndex !== -1) {
          const cleanMessage = e.message.substring(0, evaluatingIndex);
          if (cleanMessage === message) return e;
        }
      }
      assert._fail(
        `Expected to throw a ${type.name} with message "${message}", got ${e.name} with message "${e.message}"`
      );
    }
    assert._fail(`Expected to throw a ${type.name} with message "${message}"`);
  },

  instanceof: (obj, type, msg) => {
    if (!(obj instanceof type))
      assert._fail(`Expected a ${typeof type}, got ${typeof obj}`);
  },

  harnessCall: (f) => {
    if (typeof $vm !== "undefined") return f();
    console.log("WARNING: Not running inside JSC test harness");
  },

  asyncTestImpl: (promise, thenFunc, catchFunc) => {
    assert.harnessCall(() => asyncTestStart(1));
    promise.then(thenFunc).catch(catchFunc);
  },

  printExn: (e) => {
    console.log("Test failed with exception: ", e);
    console.log(e.stack);
    console.log(typeof e);
    $vm.abort();
  },

  asyncTest: (promise) =>
    assert.asyncTestImpl(
      promise,
      assert.harnessCall(() => asyncTestPassed()),
      assert.printExn
    ),

  asyncTestEq: (promise, expected) => {
    const thenCheck = (value) => {
      if (value === expected)
        return assert.harnessCall(() => asyncTestPassed());
      console.log("Failed: got ", value, " but expected ", expected);
      $vm.abort();
    };
    assert.asyncTestImpl(promise, thenCheck, assert.printExn);
  },
};

/*const _fail = (msg, extra) => {
  throw new Error(msg + (extra ? ": " + extra : ""));
};

const isNotA = (v, t, msg) => {
  if (typeof v === t) _fail(`Shouldn't be ${t}`, msg);
};

const isA = (v, t, msg) => {
  if (typeof v !== t) _fail(`Should be ${t}, got ${typeof v}`, msg);
};

const isNotUndef = (v, msg) => isNotA(v, "undefined", msg);
const isUndef = (v, msg) => isA(v, "undefined", msg);
const notObject = (v, msg) => isNotA(v, "object", msg);
const isObject = (v, msg) => isA(v, "object", msg);
const notString = (v, msg) => isNotA(v, "string", msg);
const isString = (v, msg) => isA(v, "string", msg);
const notNumber = (v, msg) => isNotA(v, "number", msg);
const isNumber = (v, msg) => isA(v, "number", msg);
const notFunction = (v, msg) => isNotA(v, "function", msg);
const isFunction = (v, msg) => isA(v, "function", msg);

const hasObjectProperty = (o, p, msg) => {
  isObject(o, msg);
  isNotUndef(o[p], msg, `expected object to have property ${p}`);
};

const isArray = (v, msg) => {
  if (!Array.isArray(v)) _fail(`Expected an array, got ${typeof v}`, msg);
};

const isNotArray = (v, msg) => {
  if (Array.isArray(v)) _fail(`Expected to not be an array`, msg);
};

const truthy = (v, msg) => {
  if (!v) _fail(`Expected truthy`, msg);
};

const falsy = (v, msg) => {
  if (v) _fail(`Expected falsy`, msg);
};

const eq = (lhs, rhs, msg) => {
  if (typeof lhs !== typeof rhs)
    _fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
  if (Array.isArray(lhs) && Array.isArray(rhs) && lhs.length === rhs.length) {
    for (let i = 0; i !== lhs.length; ++i) eq(lhs[i], rhs[i], msg);
  } else if (lhs !== rhs) {
    if (typeof lhs === "number" && isNaN(lhs) && isNaN(rhs)) return;
    _fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
  } else {
    if (typeof lhs === "number" && 1.0 / lhs !== 1.0 / rhs)
      // Distinguish -0.0 from 0.0.
      _fail(`Not the same: "${lhs}" and "${rhs}"`, msg);
  }
};

const matches = (lhs, rhs, msg) => {
  if (typeof lhs !== "string" || !(rhs instanceof RegExp))
    _fail(
      `Expected string and regex object, got ${typeof lhs} and ${typeof rhs}`,
      msg
    );
  if (!rhs.test(lhs)) _fail(`"${msg}" does not match ${rhs}`, msg);
};

const canonicalizeI32 = (number) => {
  if (Math.round(number) === number && number >= 2 ** 31)
    number = number - 2 ** 32;
  return number;
};

const eqI32 = (lhs, rhs, msg) => {
  return eq(canonicalizeI32(lhs), canonicalizeI32(rhs), msg);
};

const ge = (lhs, rhs, msg) => {
  isNotUndef(lhs);
  isNotUndef(rhs);
  if (!(lhs >= rhs)) _fail(`Expected: "${lhs}" < "${rhs}"`, msg);
};

const le = (lhs, rhs, msg) => {
  isNotUndef(lhs);
  isNotUndef(rhs);
  if (!(lhs <= rhs)) _fail(`Expected: "${lhs}" > "${rhs}"`, msg);
};

const _throws = (func, type, message, ...args) => {
  try {
    func(...args);
  } catch (e) {
    if (
      e instanceof type &&
      (typeof e.message == "undefined" || e.message.indexOf(message) >= 0)
    )
      return e;
    _fail(
      `Expected to throw a ${type.name} with message "${message}", got ${e.name} with message "${e.message}"`
    );
  }
  _fail(`Expected to throw a ${type.name} with message "${message}"`);
};

async function throwsAsync(promise, type, message) {
  try {
    await promise;
  } catch (e) {
    if (e instanceof type) {
      if (e.message === message) return e;
      // Ignore source information at the end of the error message if the
      // expected message didn't specify that information. Sometimes it
      // changes, or it's tricky to get just right.
      const evaluatingIndex = e.message.indexOf(" (evaluating '");
      if (evaluatingIndex !== -1) {
        const cleanMessage = e.message.substring(0, evaluatingIndex);
        if (cleanMessage === message) return e;
      }
    }
    _fail(
      `Expected to throw a ${type.name} with message "${message}", got ${e.name} with message "${e.message}"`
    );
  }
  _fail(`Expected to throw a ${type.name} with message "${message}"`);
}

const _instanceof = (obj, type, msg) => {
  if (!(obj instanceof type))
    _fail(`Expected a ${typeof type}, got ${typeof obj}`);
};

// Use underscore names to avoid clashing with builtin names.

function harnessCall(f) {
  if (typeof $vm !== "undefined") return f();
  console.log("WARNING: Not running inside JSC test harness");
}

const asyncTestImpl = (promise, thenFunc, catchFunc) => {
  harnessCall(() => asyncTestStart(1));
  promise.then(thenFunc).catch(catchFunc);
};

const printExn = (e) => {
  console.log("Test failed with exception: ", e);
  console.log(e.stack);
  console.log(typeof e);
  $vm.abort();
};

const asyncTest = (promise) =>
  asyncTestImpl(
    promise,
    harnessCall(() => asyncTestPassed()),
    printExn
  );
const asyncTestEq = (promise, expected) => {
  const thenCheck = (value) => {
    if (value === expected) return harnessCall(() => asyncTestPassed());
    console.log("Failed: got ", value, " but expected ", expected);
    $vm.abort();
  };
  asyncTestImpl(promise, thenCheck, printExn);
};*/

///////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////

("use strict");

// This is our nifty way to make modules synchronous.
//let assert;
/*import('./assert.js').then((module) => {
    assert = module;
}, $vm.crash);
drainMicrotasks();*/

function test(func, description) {
  try {
    func();
  } catch (e) {
    console.log("Unexpected exception:", description);
    throw e;
  }
}

function promise_test(func, description) {
  assert.asyncTest(func());
}

let assert_equals = assert.eq;
let assert_true = (x) => assert.eq(x, true);
let assert_false = (x) => assert.eq(x, false);
let assert_unreached = () => {
  throw new Error("Should have been unreachable");
};

/*let console = {
  log(...args) {
    console.log(...args);
  },
};*/

/////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////

//wasm.js

const _mapValues = (from) => {
  let values = {};
  for (const key in from) values[key] = from[key].value;
  return values;
};

const description = {
  comments: [
    "This file describes the WebAssembly ISA.",
    "Scripts in this folder auto-generate C++ code for JavaScriptCore as well as the testing DSL which WebKit's WebAssembly tests use.",
  ],
  preamble: [
    {
      name: "magic number",
      type: "uint32",
      value: 1836278016,
      description: "NULL character followed by 'asm'",
    },
    {
      name: "version",
      type: "uint32",
      value: 1,
      description: "Version number",
    },
  ],
  type: {
    i32: { type: "varint7", value: -1, b3type: "B3::Int32", width: 32 },
    i64: { type: "varint7", value: -2, b3type: "B3::Int64", width: 64 },
    f32: { type: "varint7", value: -3, b3type: "B3::Float", width: 32 },
    f64: { type: "varint7", value: -4, b3type: "B3::Double", width: 64 },
    v128: { type: "varint7", value: -5, b3type: "B3::V128", width: 128 },
    nullfuncref: { type: "varint7", value: -13, b3type: "B3::Void", width: 0 },
    nullexternref: {
      type: "varint7",
      value: -14,
      b3type: "B3::Void",
      width: 0,
    },
    nullref: { type: "varint7", value: -15, b3type: "B3::Void", width: 0 },
    funcref: {
      type: "varint7",
      value: -16,
      b3type: "B3::pointerType()",
      width: 64,
    },
    externref: {
      type: "varint7",
      value: -17,
      b3type: "B3::pointerType()",
      width: 64,
    },
    anyref: { type: "varint7", value: -18, b3type: "B3::Void", width: 0 },
    eqref: { type: "varint7", value: -19, b3type: "B3::Void", width: 0 },
    i31ref: { type: "varint7", value: -20, b3type: "B3::Void", width: 0 },
    structref: {
      type: "varint7",
      value: -21,
      b3type: "B3::pointerType()",
      width: 0,
    },
    arrayref: {
      type: "varint7",
      value: -22,
      b3type: "B3::pointerType()",
      width: 0,
    },
    ref: {
      type: "varint7",
      value: -28,
      b3type: "B3::pointerType()",
      width: 64,
    },
    ref_null: {
      type: "varint7",
      value: -29,
      b3type: "B3::pointerType()",
      width: 64,
    },
    func: { type: "varint7", value: -32, b3type: "B3::Void", width: 0 },
    struct: { type: "varint7", value: -33, b3type: "B3::Void", width: 0 },
    array: { type: "varint7", value: -34, b3type: "B3::Void", width: 0 },
    sub: { type: "varint7", value: -48, b3type: "B3::Void", width: 0 },
    subfinal: { type: "varint7", value: -49, b3type: "B3::Void", width: 0 },
    rec: { type: "varint7", value: -50, b3type: "B3::Void", width: 0 },
    void: { type: "varint7", value: -64, b3type: "B3::Void", width: 0 },
  },
  packed_type: {
    i8: { type: "varint7", value: -8 },
    i16: { type: "varint7", value: -9 },
  },
  value_type: ["i32", "i64", "f32", "f64", "externref", "funcref", "v128"],
  block_type: [
    "i32",
    "i64",
    "f32",
    "f64",
    "void",
    "externref",
    "funcref",
    "v128",
  ],
  ref_type: ["funcref", "externref", "ref", "ref_null"],
  external_kind: {
    Function: { type: "uint8", value: 0 },
    Table: { type: "uint8", value: 1 },
    Memory: { type: "uint8", value: 2 },
    Global: { type: "uint8", value: 3 },
    Exception: { type: "uint8", value: 4 },
  },
  section: {
    Type: {
      type: "varuint7",
      value: 1,
      description: "Function signature declarations",
    },
    Import: { type: "varuint7", value: 2, description: "Import declarations" },
    Function: {
      type: "varuint7",
      value: 3,
      description: "Function declarations",
    },
    Table: {
      type: "varuint7",
      value: 4,
      description: "Indirect function table and other tables",
    },
    Memory: { type: "varuint7", value: 5, description: "Memory attributes" },
    Exception: {
      type: "varuint7",
      value: 13,
      description: "Exception declarations",
    },
    Global: { type: "varuint7", value: 6, description: "Global declarations" },
    Export: { type: "varuint7", value: 7, description: "Exports" },
    Start: {
      type: "varuint7",
      value: 8,
      description: "Start function declaration",
    },
    Element: { type: "varuint7", value: 9, description: "Elements section" },
    Code: {
      type: "varuint7",
      value: 10,
      description: "Function bodies (code)",
    },
    Data: { type: "varuint7", value: 11, description: "Data segments" },
    DataCount: {
      type: "varuint7",
      value: 12,
      description: "Number of data segments",
    },
  },
  opcode: {
    unreachable: {
      category: "control",
      value: 0,
      return: [],
      parameter: [],
      immediate: [],
      description: "trap immediately",
    },
    nop: {
      category: "control",
      value: 1,
      return: [],
      parameter: [],
      immediate: [],
      description: "no operation",
    },
    block: {
      category: "control",
      value: 2,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "sig", type: "block_type" }],
      description: "begin a sequence of expressions, yielding 0 or 1 values",
    },
    loop: {
      category: "control",
      value: 3,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "sig", type: "block_type" }],
      description: "begin a block which can also form control flow loops",
    },
    if: {
      category: "control",
      value: 4,
      return: ["control"],
      parameter: ["bool"],
      immediate: [{ name: "sig", type: "block_type" }],
      description: "begin if expression",
    },
    else: {
      category: "control",
      value: 5,
      return: ["control"],
      parameter: [],
      immediate: [],
      description: "begin else expression of if",
    },
    try: {
      category: "control",
      value: 6,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "sig", type: "block_type" }],
      description: "begin try expression",
    },
    catch: {
      category: "control",
      value: 7,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "exn", type: "varuint32" }],
      description: "begin catch expression of try",
    },
    throw: {
      category: "control",
      value: 8,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "exn", type: "varuint32" }],
      description: "throw exception",
    },
    rethrow: {
      category: "control",
      value: 9,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "rethrow the exception at the top of the stack",
    },
    br: {
      category: "control",
      value: 12,
      return: [],
      parameter: [],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "break that targets an outer nested block",
    },
    br_if: {
      category: "control",
      value: 13,
      return: [],
      parameter: [],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "conditional break that targets an outer nested block",
    },
    br_table: {
      category: "control",
      value: 14,
      return: [],
      parameter: [],
      immediate: [
        {
          name: "target_count",
          type: "varuint32",
          description: "number of entries in the target_table",
        },
        {
          name: "target_table",
          type: "varuint32*",
          description:
            "target entries that indicate an outer block or loop to which to break",
        },
        {
          name: "default_target",
          type: "varuint32",
          description:
            "an outer block or loop to which to break in the default case",
        },
      ],
      description: "branch table control flow construct",
    },
    return: {
      category: "control",
      value: 15,
      return: [],
      parameter: [],
      immediate: [],
      description: "return zero or one value from this function",
    },
    delegate: {
      category: "control",
      value: 24,
      return: ["control"],
      parameter: [],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "delegate to a parent try block",
    },
    catch_all: {
      category: "control",
      value: 25,
      return: ["control"],
      parameter: [],
      immediate: [],
      description: "catch exceptions regardless of tag",
    },
    drop: {
      category: "control",
      value: 26,
      return: [],
      parameter: ["any"],
      immediate: [],
      description: "ignore value",
    },
    select: {
      category: "control",
      value: 27,
      return: ["prev"],
      parameter: ["any", "prev", "bool"],
      immediate: [],
      description: "select one of two values based on condition",
    },
    annotated_select: {
      category: "control",
      value: 28,
      return: ["prev"],
      parameter: ["any", "prev", "bool"],
      immediate: [
        {
          name: "target_types_count",
          type: "varuint32",
          description: "number of entries in the target types vector",
        },
        {
          name: "target_types",
          type: "value_type*",
          description:
            "target types that indicate result of select instruction",
        },
      ],
      description:
        "the same as just select but with the annotation for result types",
    },
    end: {
      category: "control",
      value: 11,
      return: [],
      parameter: [],
      immediate: [],
      description: "end a block, loop, or if",
    },
    "i32.const": {
      category: "special",
      value: 65,
      return: ["i32"],
      parameter: [],
      immediate: [{ name: "value", type: "varint32" }],
      description: "a constant value interpreted as i32",
    },
    "i64.const": {
      category: "special",
      value: 66,
      return: ["i64"],
      parameter: [],
      immediate: [{ name: "value", type: "varint64" }],
      description: "a constant value interpreted as i64",
    },
    "f64.const": {
      category: "special",
      value: 68,
      return: ["f64"],
      parameter: [],
      immediate: [{ name: "value", type: "double" }],
      description: "a constant value interpreted as f64",
    },
    "f32.const": {
      category: "special",
      value: 67,
      return: ["f32"],
      parameter: [],
      immediate: [{ name: "value", type: "float" }],
      description: "a constant value interpreted as f32",
    },
    "ref.null": {
      category: "special",
      value: 208,
      return: ["externref", "funcref"],
      parameter: [],
      immediate: [{ name: "reftype", type: "ref_type" }],
      description: "a constant null reference",
    },
    "ref.is_null": {
      category: "special",
      value: 209,
      return: ["i32"],
      parameter: ["externref"],
      immediate: [],
      description: "determine if a reference is null",
    },
    "ref.func": {
      category: "special",
      value: 210,
      return: ["funcref"],
      parameter: [],
      immediate: [{ name: "function_index", type: "varuint32" }],
      description: "return a reference to the function at the given index",
    },
    "ref.eq": {
      category: "special",
      value: 211,
      return: ["i32"],
      parameter: ["eqref", "eqref"],
      immediate: [],
      description: "determine if the argument references are equal",
    },
    "ref.as_non_null": {
      category: "special",
      value: 212,
      return: ["any"],
      parameter: ["any"],
      immediate: [],
      description: "return the reference with non-null type or trap if null",
    },
    br_on_null: {
      category: "control",
      value: 213,
      return: [""],
      parameter: ["any"],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "break to an outer block if the reference is null",
    },
    br_on_non_null: {
      category: "control",
      value: 214,
      return: [""],
      parameter: ["any"],
      immediate: [{ name: "relative_depth", type: "varuint32" }],
      description: "break to an outer block if the reference is non-null",
    },
    get_local: {
      category: "special",
      value: 32,
      return: ["any"],
      parameter: [],
      immediate: [{ name: "local_index", type: "varuint32" }],
      description: "read a local variable or parameter",
    },
    set_local: {
      category: "special",
      value: 33,
      return: [],
      parameter: ["any"],
      immediate: [{ name: "local_index", type: "varuint32" }],
      description: "write a local variable or parameter",
    },
    tee_local: {
      category: "special",
      value: 34,
      return: ["any"],
      parameter: ["any"],
      immediate: [{ name: "local_index", type: "varuint32" }],
      description:
        "write a local variable or parameter and return the same value",
    },
    get_global: {
      category: "special",
      value: 35,
      return: ["any"],
      parameter: [],
      immediate: [{ name: "global_index", type: "varuint32" }],
      description: "read a global variable",
    },
    set_global: {
      category: "special",
      value: 36,
      return: [],
      parameter: ["any"],
      immediate: [{ name: "global_index", type: "varuint32" }],
      description: "write a global variable",
    },
    "table.get": {
      category: "special",
      value: 37,
      return: ["externref"],
      parameter: ["i32"],
      immediate: [{ name: "table_index", type: "varuint32" }],
      description: "get a table value",
    },
    "table.set": {
      category: "special",
      value: 38,
      return: [],
      parameter: ["i32", "externref"],
      immediate: [{ name: "table_index", type: "varuint32" }],
      description: "set a table value",
    },
    "table.init": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "i32", "i32"],
      immediate: [
        { name: "element_index", type: "varuint32" },
        { name: "table_index", type: "varuint32" },
      ],
      description: "initialize table from a given element",
      extendedOp: 12,
    },
    "elem.drop": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: [],
      immediate: [{ name: "element_index", type: "varuint32" }],
      description: "prevents further use of a passive element segment",
      extendedOp: 13,
    },
    "table.grow": {
      category: "exttable",
      value: 252,
      return: ["i32"],
      parameter: ["externref", "i32"],
      immediate: [{ name: "table_index", type: "varuint32" }],
      description:
        "grow a table by the given delta and return the previous size, or -1 if enough space cannot be allocated",
      extendedOp: 15,
    },
    "table.size": {
      category: "exttable",
      value: 252,
      return: ["i32"],
      parameter: [],
      immediate: [{ name: "table_index", type: "varuint32" }],
      description: "get the size of a table",
      extendedOp: 16,
    },
    "table.fill": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "externref", "i32"],
      immediate: [{ name: "table_index", type: "varuint32" }],
      description: "fill entries [i,i+n) with the given value",
      extendedOp: 17,
    },
    "table.copy": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "i32", "i32"],
      immediate: [
        { name: "dst_index", type: "varuint32" },
        { name: "src_index", type: "varuint32" },
      ],
      description:
        "copy table elements from dst_table[dstOffset, dstOffset + length] to src_table[srcOffset, srcOffset + length]",
      extendedOp: 14,
    },
    "memory.fill": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "i32", "i32"],
      immediate: [{ name: "unused", type: "uint8" }],
      description: "sets all values in a region to a given byte",
      extendedOp: 11,
    },
    "memory.copy": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "i32", "i32"],
      immediate: [
        { name: "unused", type: "uint8" },
        { name: "unused", type: "uint8" },
      ],
      description:
        "copies data from a source memory region to destination region",
      extendedOp: 10,
    },
    "memory.init": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: ["i32", "i32", "i32"],
      immediate: [
        { name: "segment_index", type: "varuint32" },
        { name: "unsued", type: "varuint32" },
      ],
      description: "copies data from a passive data segment into a memory",
      extendedOp: 8,
    },
    "data.drop": {
      category: "exttable",
      value: 252,
      return: [],
      parameter: [],
      immediate: [{ name: "segment_index", type: "varuint32" }],
      description: "shrinks the size of the segment to zero",
      extendedOp: 9,
    },
    call: {
      category: "call",
      value: 16,
      return: ["call"],
      parameter: ["call"],
      immediate: [{ name: "function_index", type: "varuint32" }],
      description: "call a function by its index",
    },
    call_indirect: {
      category: "call",
      value: 17,
      return: ["call"],
      parameter: ["call"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "table_index", type: "varuint32" },
      ],
      description: "call a function indirect with an expected signature",
    },
    tail_call: {
      category: "call",
      value: 18,
      return: ["call"],
      parameter: ["call"],
      immediate: [{ name: "function_index", type: "varuint32" }],
      description: "tail call a function by its index",
    },
    tail_call_indirect: {
      category: "call",
      value: 19,
      return: ["call"],
      parameter: ["call"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "table_index", type: "varuint32" },
      ],
      description: "indirect tail call a function with an expected signature",
    },
    call_ref: {
      category: "call",
      value: 20,
      return: ["call"],
      parameter: ["call"],
      immediate: [],
      description: "call a function reference",
    },
    "i32.load8_s": {
      category: "memory",
      value: 44,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i32.load8_u": {
      category: "memory",
      value: 45,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i32.load16_s": {
      category: "memory",
      value: 46,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i32.load16_u": {
      category: "memory",
      value: 47,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load8_s": {
      category: "memory",
      value: 48,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load8_u": {
      category: "memory",
      value: 49,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load16_s": {
      category: "memory",
      value: 50,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load16_u": {
      category: "memory",
      value: 51,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load32_s": {
      category: "memory",
      value: 52,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load32_u": {
      category: "memory",
      value: 53,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i32.load": {
      category: "memory",
      value: 40,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i64.load": {
      category: "memory",
      value: 41,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "f32.load": {
      category: "memory",
      value: 42,
      return: ["f32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "f64.load": {
      category: "memory",
      value: 43,
      return: ["f64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "load from memory",
    },
    "i32.store8": {
      category: "memory",
      value: 58,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i32.store16": {
      category: "memory",
      value: 59,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i64.store8": {
      category: "memory",
      value: 60,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i64.store16": {
      category: "memory",
      value: 61,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i64.store32": {
      category: "memory",
      value: 62,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i32.store": {
      category: "memory",
      value: 54,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "i64.store": {
      category: "memory",
      value: 55,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "f32.store": {
      category: "memory",
      value: 56,
      return: [],
      parameter: ["addr", "f32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    "f64.store": {
      category: "memory",
      value: 57,
      return: [],
      parameter: ["addr", "f64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      description: "store to memory",
    },
    current_memory: {
      category: "operation",
      value: 63,
      return: ["size"],
      parameter: [],
      immediate: [{ name: "flags", type: "uint8" }],
      description: "query the size of memory",
    },
    grow_memory: {
      category: "operation",
      value: 64,
      return: ["size"],
      parameter: ["size"],
      immediate: [{ name: "flags", type: "uint8" }],
      description: "grow the size of memory",
    },
    "i32.add": {
      category: "arithmetic",
      value: 106,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Add",
    },
    "i32.sub": {
      category: "arithmetic",
      value: 107,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Sub",
    },
    "i32.mul": {
      category: "arithmetic",
      value: 108,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Mul",
    },
    "i32.div_s": {
      category: "arithmetic",
      value: 109,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
    },
    "i32.div_u": {
      category: "arithmetic",
      value: 110,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
    },
    "i32.rem_s": {
      category: "arithmetic",
      value: 111,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
    },
    "i32.rem_u": {
      category: "arithmetic",
      value: 112,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
    },
    "i32.and": {
      category: "arithmetic",
      value: 113,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "BitAnd",
    },
    "i32.or": {
      category: "arithmetic",
      value: 114,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "BitOr",
    },
    "i32.xor": {
      category: "arithmetic",
      value: 115,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "BitXor",
    },
    "i32.shl": {
      category: "arithmetic",
      value: 116,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Shl",
    },
    "i32.shr_u": {
      category: "arithmetic",
      value: 118,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "ZShr",
    },
    "i32.shr_s": {
      category: "arithmetic",
      value: 117,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "SShr",
    },
    "i32.rotr": {
      category: "arithmetic",
      value: 120,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "RotR",
    },
    "i32.rotl": {
      category: "arithmetic",
      value: 119,
      return: ["i32"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "RotL",
    },
    "i32.eq": {
      category: "comparison",
      value: 70,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Equal",
    },
    "i32.ne": {
      category: "comparison",
      value: 71,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "NotEqual",
    },
    "i32.lt_s": {
      category: "comparison",
      value: 72,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "LessThan",
    },
    "i32.le_s": {
      category: "comparison",
      value: 76,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "LessEqual",
    },
    "i32.lt_u": {
      category: "comparison",
      value: 73,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Below",
    },
    "i32.le_u": {
      category: "comparison",
      value: 77,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "BelowEqual",
    },
    "i32.gt_s": {
      category: "comparison",
      value: 74,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "GreaterThan",
    },
    "i32.ge_s": {
      category: "comparison",
      value: 78,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "GreaterEqual",
    },
    "i32.gt_u": {
      category: "comparison",
      value: 75,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "Above",
    },
    "i32.ge_u": {
      category: "comparison",
      value: 79,
      return: ["bool"],
      parameter: ["i32", "i32"],
      immediate: [],
      b3op: "AboveEqual",
    },
    "i32.clz": {
      category: "arithmetic",
      value: 103,
      return: ["i32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "Clz",
    },
    "i32.ctz": {
      category: "arithmetic",
      value: 104,
      return: ["i32"],
      parameter: ["i32"],
      immediate: [],
    },
    "i32.popcnt": {
      category: "arithmetic",
      value: 105,
      return: ["i32"],
      parameter: ["i32"],
      immediate: [],
    },
    "i32.eqz": {
      category: "comparison",
      value: 69,
      return: ["bool"],
      parameter: ["i32"],
      immediate: [],
      b3op: "Equal(i32(0), @0)",
    },
    "i64.add": {
      category: "arithmetic",
      value: 124,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Add",
    },
    "i64.sub": {
      category: "arithmetic",
      value: 125,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Sub",
    },
    "i64.mul": {
      category: "arithmetic",
      value: 126,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Mul",
    },
    "i64.div_s": {
      category: "arithmetic",
      value: 127,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
    },
    "i64.div_u": {
      category: "arithmetic",
      value: 128,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
    },
    "i64.rem_s": {
      category: "arithmetic",
      value: 129,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
    },
    "i64.rem_u": {
      category: "arithmetic",
      value: 130,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
    },
    "i64.and": {
      category: "arithmetic",
      value: 131,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "BitAnd",
    },
    "i64.or": {
      category: "arithmetic",
      value: 132,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "BitOr",
    },
    "i64.xor": {
      category: "arithmetic",
      value: 133,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "BitXor",
    },
    "i64.shl": {
      category: "arithmetic",
      value: 134,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Shl(@0, Trunc(@1))",
    },
    "i64.shr_u": {
      category: "arithmetic",
      value: 136,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "ZShr(@0, Trunc(@1))",
    },
    "i64.shr_s": {
      category: "arithmetic",
      value: 135,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "SShr(@0, Trunc(@1))",
    },
    "i64.rotr": {
      category: "arithmetic",
      value: 138,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "RotR(@0, Trunc(@1))",
    },
    "i64.rotl": {
      category: "arithmetic",
      value: 137,
      return: ["i64"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "RotL(@0, Trunc(@1))",
    },
    "i64.eq": {
      category: "comparison",
      value: 81,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Equal",
    },
    "i64.ne": {
      category: "comparison",
      value: 82,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "NotEqual",
    },
    "i64.lt_s": {
      category: "comparison",
      value: 83,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "LessThan",
    },
    "i64.le_s": {
      category: "comparison",
      value: 87,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "LessEqual",
    },
    "i64.lt_u": {
      category: "comparison",
      value: 84,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Below",
    },
    "i64.le_u": {
      category: "comparison",
      value: 88,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "BelowEqual",
    },
    "i64.gt_s": {
      category: "comparison",
      value: 85,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "GreaterThan",
    },
    "i64.ge_s": {
      category: "comparison",
      value: 89,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "GreaterEqual",
    },
    "i64.gt_u": {
      category: "comparison",
      value: 86,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "Above",
    },
    "i64.ge_u": {
      category: "comparison",
      value: 90,
      return: ["bool"],
      parameter: ["i64", "i64"],
      immediate: [],
      b3op: "AboveEqual",
    },
    "i64.clz": {
      category: "arithmetic",
      value: 121,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "Clz",
    },
    "i64.ctz": {
      category: "arithmetic",
      value: 122,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
    },
    "i64.popcnt": {
      category: "arithmetic",
      value: 123,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
    },
    "i64.eqz": {
      category: "comparison",
      value: 80,
      return: ["bool"],
      parameter: ["i64"],
      immediate: [],
      b3op: "Equal(i64(0), @0)",
    },
    "f32.add": {
      category: "arithmetic",
      value: 146,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "Add",
    },
    "f32.sub": {
      category: "arithmetic",
      value: 147,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "Sub",
    },
    "f32.mul": {
      category: "arithmetic",
      value: 148,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "Mul",
    },
    "f32.div": {
      category: "arithmetic",
      value: 149,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "Div",
    },
    "f32.min": {
      category: "arithmetic",
      value: 150,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "FMin",
    },
    "f32.max": {
      category: "arithmetic",
      value: 151,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "FMax",
    },
    "f32.abs": {
      category: "arithmetic",
      value: 139,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "Abs",
    },
    "f32.neg": {
      category: "arithmetic",
      value: 140,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "Neg",
    },
    "f32.copysign": {
      category: "arithmetic",
      value: 152,
      return: ["f32"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "BitwiseCast(BitOr(BitAnd(BitwiseCast(@1), i32(0x80000000)), BitAnd(BitwiseCast(@0), i32(0x7fffffff))))",
    },
    "f32.ceil": {
      category: "arithmetic",
      value: 141,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "Ceil",
    },
    "f32.floor": {
      category: "arithmetic",
      value: 142,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "Floor",
    },
    "f32.trunc": {
      category: "arithmetic",
      value: 143,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
    },
    "f32.nearest": {
      category: "arithmetic",
      value: 144,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
    },
    "f32.sqrt": {
      category: "arithmetic",
      value: 145,
      return: ["f32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "Sqrt",
    },
    "f32.eq": {
      category: "comparison",
      value: 91,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "Equal",
    },
    "f32.ne": {
      category: "comparison",
      value: 92,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "NotEqual",
    },
    "f32.lt": {
      category: "comparison",
      value: 93,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "LessThan",
    },
    "f32.le": {
      category: "comparison",
      value: 95,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "LessEqual",
    },
    "f32.gt": {
      category: "comparison",
      value: 94,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "GreaterThan",
    },
    "f32.ge": {
      category: "comparison",
      value: 96,
      return: ["bool"],
      parameter: ["f32", "f32"],
      immediate: [],
      b3op: "GreaterEqual",
    },
    "f64.add": {
      category: "arithmetic",
      value: 160,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "Add",
    },
    "f64.sub": {
      category: "arithmetic",
      value: 161,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "Sub",
    },
    "f64.mul": {
      category: "arithmetic",
      value: 162,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "Mul",
    },
    "f64.div": {
      category: "arithmetic",
      value: 163,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "Div",
    },
    "f64.min": {
      category: "arithmetic",
      value: 164,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "FMin",
    },
    "f64.max": {
      category: "arithmetic",
      value: 165,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "FMax",
    },
    "f64.abs": {
      category: "arithmetic",
      value: 153,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "Abs",
    },
    "f64.neg": {
      category: "arithmetic",
      value: 154,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "Neg",
    },
    "f64.copysign": {
      category: "arithmetic",
      value: 166,
      return: ["f64"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "BitwiseCast(BitOr(BitAnd(BitwiseCast(@1), i64(0x8000000000000000)), BitAnd(BitwiseCast(@0), i64(0x7fffffffffffffff))))",
    },
    "f64.ceil": {
      category: "arithmetic",
      value: 155,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "Ceil",
    },
    "f64.floor": {
      category: "arithmetic",
      value: 156,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "Floor",
    },
    "f64.trunc": {
      category: "arithmetic",
      value: 157,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
    },
    "f64.nearest": {
      category: "arithmetic",
      value: 158,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
    },
    "f64.sqrt": {
      category: "arithmetic",
      value: 159,
      return: ["f64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "Sqrt",
    },
    "f64.eq": {
      category: "comparison",
      value: 97,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "Equal",
    },
    "f64.ne": {
      category: "comparison",
      value: 98,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "NotEqual",
    },
    "f64.lt": {
      category: "comparison",
      value: 99,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "LessThan",
    },
    "f64.le": {
      category: "comparison",
      value: 101,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "LessEqual",
    },
    "f64.gt": {
      category: "comparison",
      value: 100,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "GreaterThan",
    },
    "f64.ge": {
      category: "comparison",
      value: 102,
      return: ["bool"],
      parameter: ["f64", "f64"],
      immediate: [],
      b3op: "GreaterEqual",
    },
    "i32.trunc_s/f32": {
      category: "conversion",
      value: 168,
      return: ["i32"],
      parameter: ["f32"],
      immediate: [],
    },
    "i32.trunc_s/f64": {
      category: "conversion",
      value: 170,
      return: ["i32"],
      parameter: ["f64"],
      immediate: [],
    },
    "i32.trunc_u/f32": {
      category: "conversion",
      value: 169,
      return: ["i32"],
      parameter: ["f32"],
      immediate: [],
    },
    "i32.trunc_u/f64": {
      category: "conversion",
      value: 171,
      return: ["i32"],
      parameter: ["f64"],
      immediate: [],
    },
    "i32.wrap/i64": {
      category: "conversion",
      value: 167,
      return: ["i32"],
      parameter: ["i64"],
      immediate: [],
      b3op: "Trunc",
    },
    "i64.trunc_s/f32": {
      category: "conversion",
      value: 174,
      return: ["i64"],
      parameter: ["f32"],
      immediate: [],
    },
    "i64.trunc_s/f64": {
      category: "conversion",
      value: 176,
      return: ["i64"],
      parameter: ["f64"],
      immediate: [],
    },
    "i64.trunc_u/f32": {
      category: "conversion",
      value: 175,
      return: ["i64"],
      parameter: ["f32"],
      immediate: [],
    },
    "i64.trunc_u/f64": {
      category: "conversion",
      value: 177,
      return: ["i64"],
      parameter: ["f64"],
      immediate: [],
    },
    "i64.extend_s/i32": {
      category: "conversion",
      value: 172,
      return: ["i64"],
      parameter: ["i32"],
      immediate: [],
      b3op: "SExt32",
    },
    "i64.extend_u/i32": {
      category: "conversion",
      value: 173,
      return: ["i64"],
      parameter: ["i32"],
      immediate: [],
      b3op: "ZExt32",
    },
    "f32.convert_s/i32": {
      category: "conversion",
      value: 178,
      return: ["f32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "IToF",
    },
    "f32.convert_u/i32": {
      category: "conversion",
      value: 179,
      return: ["f32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "IToF(ZExt32(@0))",
    },
    "f32.convert_s/i64": {
      category: "conversion",
      value: 180,
      return: ["f32"],
      parameter: ["i64"],
      immediate: [],
      b3op: "IToF",
    },
    "f32.convert_u/i64": {
      category: "conversion",
      value: 181,
      return: ["f32"],
      parameter: ["i64"],
      immediate: [],
    },
    "f32.demote/f64": {
      category: "conversion",
      value: 182,
      return: ["f32"],
      parameter: ["f64"],
      immediate: [],
      b3op: "DoubleToFloat",
    },
    "f32.reinterpret/i32": {
      category: "conversion",
      value: 190,
      return: ["f32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "BitwiseCast",
    },
    "f64.convert_s/i32": {
      category: "conversion",
      value: 183,
      return: ["f64"],
      parameter: ["i32"],
      immediate: [],
      b3op: "IToD",
    },
    "f64.convert_u/i32": {
      category: "conversion",
      value: 184,
      return: ["f64"],
      parameter: ["i32"],
      immediate: [],
      b3op: "IToD(ZExt32(@0))",
    },
    "f64.convert_s/i64": {
      category: "conversion",
      value: 185,
      return: ["f64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "IToD",
    },
    "f64.convert_u/i64": {
      category: "conversion",
      value: 186,
      return: ["f64"],
      parameter: ["i64"],
      immediate: [],
    },
    "f64.promote/f32": {
      category: "conversion",
      value: 187,
      return: ["f64"],
      parameter: ["f32"],
      immediate: [],
      b3op: "FloatToDouble",
    },
    "f64.reinterpret/i64": {
      category: "conversion",
      value: 191,
      return: ["f64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "BitwiseCast",
    },
    "i32.reinterpret/f32": {
      category: "conversion",
      value: 188,
      return: ["i32"],
      parameter: ["f32"],
      immediate: [],
      b3op: "BitwiseCast",
    },
    "i64.reinterpret/f64": {
      category: "conversion",
      value: 189,
      return: ["i64"],
      parameter: ["f64"],
      immediate: [],
      b3op: "BitwiseCast",
    },
    "i32.extend8_s": {
      category: "conversion",
      value: 192,
      return: ["i32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "SExt8",
    },
    "i32.extend16_s": {
      category: "conversion",
      value: 193,
      return: ["i32"],
      parameter: ["i32"],
      immediate: [],
      b3op: "SExt16",
    },
    "i64.extend8_s": {
      category: "conversion",
      value: 194,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "SExt32(SExt8(Trunc(@0)))",
    },
    "i64.extend16_s": {
      category: "conversion",
      value: 195,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "SExt32(SExt16(Trunc(@0)))",
    },
    "i64.extend32_s": {
      category: "conversion",
      value: 196,
      return: ["i64"],
      parameter: ["i64"],
      immediate: [],
      b3op: "SExt32(Trunc(@0))",
    },

    "struct.new": {
      category: "gc",
      value: 251,
      return: ["ref_type"],
      parameter: [],
      immediate: [{ name: "type_index", type: "varuint32" }],
      description: "allocates a new structure",
      extendedOp: 0,
    },
    "struct.new_default": {
      category: "gc",
      value: 251,
      return: ["ref_type"],
      parameter: [],
      immediate: [{ name: "type_index", type: "varuint32" }],
      description: "allocates a new structure with default field values",
      extendedOp: 1,
    },
    "struct.get": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: [],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "field_index", type: "varuint32" },
      ],
      description: "reads the field from a structure",
      extendedOp: 2,
    },
    "struct.get_s": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: [],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "field_index", type: "varuint32" },
      ],
      description: "reads the field from a structure",
      extendedOp: 3,
    },
    "struct.get_u": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: [],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "field_index", type: "varuint32" },
      ],
      description: "reads the field from a structure",
      extendedOp: 4,
    },
    "struct.set": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["ref_type"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "field_index", type: "varuint32" },
      ],
      description: "sets the field from a structure",
      extendedOp: 5,
    },
    "array.new": {
      category: "gc",
      value: 251,
      return: ["arrayref"],
      parameter: ["any", "i32", "rtt"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 6,
    },
    "array.new_default": {
      category: "gc",
      value: 251,
      return: ["arrayref"],
      parameter: ["i32", "rtt"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 7,
    },
    "array.new_fixed": {
      category: "gc",
      value: 251,
      return: ["arrayref"],
      parameter: ["rtt"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "argument_length", type: "varuint32" },
      ],
      extendedOp: 8,
    },
    "array.new_data": {
      category: "gc",
      value: 251,
      return: ["arrayref"],
      parameter: ["i32", "i32"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "data_index", type: "varuint32" },
      ],
      extendedOp: 9,
    },
    "array.new_elem": {
      category: "gc",
      value: 251,
      return: ["arrayref"],
      parameter: ["i32", "i32"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "data_index", type: "varuint32" },
      ],
      extendedOp: 10,
    },
    "array.get": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["arrayref", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 11,
    },
    "array.get_s": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["arrayref", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 12,
    },
    "array.get_u": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["arrayref", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 13,
    },
    "array.set": {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["arrayref", "i32", "any"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 14,
    },
    "array.len": {
      category: "gc",
      value: 251,
      return: ["i32"],
      parameter: ["arrayref"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 15,
    },
    "array.fill": {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["arrayref", "i32", "any", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 16,
    },
    "array.copy": {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["arrayref", "i32", "arrayref", "i32", "i32"],
      immediate: [
        { name: "type_index", type: "varuint32" },
        { name: "type_index", type: "varuint32" },
      ],
      extendedOp: 17,
    },
    "array.init_data": {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["arrayref", "i32", "i32", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 18,
    },
    "array.init_elem": {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["arrayref", "i32", "i32", "i32"],
      immediate: [{ name: "type_index", type: "varuint32" }],
      extendedOp: 19,
    },
    "ref.test": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["any"],
      immediate: [{ name: "heap_type", type: "varuint32" }],
      extendedOp: 20,
    },
    "ref.test_null": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["any"],
      immediate: [{ name: "heap_type", type: "varuint32" }],
      extendedOp: 21,
    },
    "ref.cast": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["any"],
      immediate: [{ name: "heap_type", type: "varuint32" }],
      extendedOp: 22,
    },
    "ref.cast_null": {
      category: "gc",
      value: 251,
      return: ["any"],
      parameter: ["any"],
      immediate: [{ name: "heap_type", type: "varuint32" }],
      extendedOp: 23,
    },
    br_on_cast: {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["any"],
      immediate: [
        { name: "flags", type: "uint8" },
        { name: "relative_depth", type: "varuint32" },
        { name: "heap_type1", type: "varuint32" },
        { name: "heap_type2", type: "varuint32" },
      ],
      extendedOp: 24,
    },
    br_on_cast_fail: {
      category: "gc",
      value: 251,
      return: [],
      parameter: ["any"],
      immediate: [
        { name: "flags", type: "uint8" },
        { name: "relative_depth", type: "varuint32" },
        { name: "heap_type1", type: "varuint32" },
        { name: "heap_type2", type: "varuint32" },
      ],
      extendedOp: 25,
    },
    "any.convert_extern": {
      category: "gc",
      value: 251,
      return: ["anyref"],
      parameter: ["externref"],
      immediate: [],
      extendedOp: 26,
    },
    "extern.convert_any": {
      category: "gc",
      value: 251,
      return: ["externref"],
      parameter: ["anyref"],
      immediate: [],
      extendedOp: 27,
    },
    "ref.i31": {
      category: "gc",
      value: 251,
      return: ["i31ref"],
      parameter: ["i32"],
      immediate: [],
      extendedOp: 28,
    },
    "i31.get_s": {
      category: "gc",
      value: 251,
      return: ["i32"],
      parameter: ["i31ref"],
      immediate: [],
      extendedOp: 29,
    },
    "i31.get_u": {
      category: "gc",
      value: 251,
      return: ["i32"],
      parameter: ["i31ref"],
      immediate: [],
      extendedOp: 30,
    },

    "i32.trunc_sat_f32_s": {
      category: "conversion",
      value: 252,
      return: ["i32"],
      parameter: ["f32"],
      immediate: [],
      extendedOp: 0,
    },
    "i32.trunc_sat_f32_u": {
      category: "conversion",
      value: 252,
      return: ["i32"],
      parameter: ["f32"],
      immediate: [],
      extendedOp: 1,
    },
    "i32.trunc_sat_f64_s": {
      category: "conversion",
      value: 252,
      return: ["i32"],
      parameter: ["f64"],
      immediate: [],
      extendedOp: 2,
    },
    "i32.trunc_sat_f64_u": {
      category: "conversion",
      value: 252,
      return: ["i32"],
      parameter: ["f64"],
      immediate: [],
      extendedOp: 3,
    },
    "i64.trunc_sat_f32_s": {
      category: "conversion",
      value: 252,
      return: ["i64"],
      parameter: ["f32"],
      immediate: [],
      extendedOp: 4,
    },
    "i64.trunc_sat_f32_u": {
      category: "conversion",
      value: 252,
      return: ["i64"],
      parameter: ["f32"],
      immediate: [],
      extendedOp: 5,
    },
    "i64.trunc_sat_f64_s": {
      category: "conversion",
      value: 252,
      return: ["i64"],
      parameter: ["f64"],
      immediate: [],
      extendedOp: 6,
    },
    "i64.trunc_sat_f64_u": {
      category: "conversion",
      value: 252,
      return: ["i64"],
      parameter: ["f64"],
      immediate: [],
      extendedOp: 7,
    },

    "memory.atomic.notify": {
      category: "atomic",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 0,
    },
    "memory.atomic.wait32": {
      category: "atomic",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 1,
    },
    "memory.atomic.wait64": {
      category: "atomic",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i64", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 2,
    },
    "atomic.fence": {
      category: "atomic",
      value: 254,
      return: [],
      parameter: [],
      immediate: [{ name: "flags", type: "uint8" }],
      extendedOp: 3,
    },
    "i32.atomic.load": {
      category: "atomic.load",
      value: 254,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 16,
    },
    "i64.atomic.load": {
      category: "atomic.load",
      value: 254,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 17,
    },
    "i32.atomic.load8_u": {
      category: "atomic.load",
      value: 254,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 18,
    },
    "i32.atomic.load16_u": {
      category: "atomic.load",
      value: 254,
      return: ["i32"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 19,
    },
    "i64.atomic.load8_u": {
      category: "atomic.load",
      value: 254,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 20,
    },
    "i64.atomic.load16_u": {
      category: "atomic.load",
      value: 254,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 21,
    },
    "i64.atomic.load32_u": {
      category: "atomic.load",
      value: 254,
      return: ["i64"],
      parameter: ["addr"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 22,
    },
    "i32.atomic.store": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 23,
    },
    "i64.atomic.store": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 24,
    },
    "i32.atomic.store8_u": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 25,
    },
    "i32.atomic.store16_u": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 26,
    },
    "i64.atomic.store8_u": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 27,
    },
    "i64.atomic.store16_u": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 28,
    },
    "i64.atomic.store32_u": {
      category: "atomic.store",
      value: 254,
      return: [],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 29,
    },
    "i32.atomic.rmw.add": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 30,
    },
    "i64.atomic.rmw.add": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 31,
    },
    "i32.atomic.rmw8.add_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 32,
    },
    "i32.atomic.rmw16.add_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 33,
    },
    "i64.atomic.rmw8.add_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 34,
    },
    "i64.atomic.rmw16.add_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 35,
    },
    "i64.atomic.rmw32.add_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 36,
    },
    "i32.atomic.rmw.sub": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 37,
    },
    "i64.atomic.rmw.sub": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 38,
    },
    "i32.atomic.rmw8.sub_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 39,
    },
    "i32.atomic.rmw16.sub_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 40,
    },
    "i64.atomic.rmw8.sub_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 41,
    },
    "i64.atomic.rmw16.sub_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 42,
    },
    "i64.atomic.rmw32.sub_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 43,
    },
    "i32.atomic.rmw.and": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 44,
    },
    "i64.atomic.rmw.and": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 45,
    },
    "i32.atomic.rmw8.and_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 46,
    },
    "i32.atomic.rmw16.and_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 47,
    },
    "i64.atomic.rmw8.and_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 48,
    },
    "i64.atomic.rmw16.and_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 49,
    },
    "i64.atomic.rmw32.and_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 50,
    },
    "i32.atomic.rmw.or": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 51,
    },
    "i64.atomic.rmw.or": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 52,
    },
    "i32.atomic.rmw8.or_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 53,
    },
    "i32.atomic.rmw16.or_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 54,
    },
    "i64.atomic.rmw8.or_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 55,
    },
    "i64.atomic.rmw16.or_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 56,
    },
    "i64.atomic.rmw32.or_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 57,
    },
    "i32.atomic.rmw.xor": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 58,
    },
    "i64.atomic.rmw.xor": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 59,
    },
    "i32.atomic.rmw8.xor_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 60,
    },
    "i32.atomic.rmw16.xor_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 61,
    },
    "i64.atomic.rmw8.xor_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 62,
    },
    "i64.atomic.rmw16.xor_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 63,
    },
    "i64.atomic.rmw32.xor_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 64,
    },
    "i32.atomic.rmw.xchg": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 65,
    },
    "i64.atomic.rmw.xchg": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 66,
    },
    "i32.atomic.rmw8.xchg_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 67,
    },
    "i32.atomic.rmw16.xchg_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 68,
    },
    "i64.atomic.rmw8.xchg_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 69,
    },
    "i64.atomic.rmw16.xchg_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 70,
    },
    "i64.atomic.rmw32.xchg_u": {
      category: "atomic.rmw.binary",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 71,
    },
    "i32.atomic.rmw.cmpxchg": {
      category: "atomic.rmw",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 72,
    },
    "i64.atomic.rmw.cmpxchg": {
      category: "atomic.rmw",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 73,
    },
    "i32.atomic.rmw8.cmpxchg_u": {
      category: "atomic.rmw",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 74,
    },
    "i32.atomic.rmw16.cmpxchg_u": {
      category: "atomic.rmw",
      value: 254,
      return: ["i32"],
      parameter: ["addr", "i32", "i32"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 75,
    },
    "i64.atomic.rmw8.cmpxchg_u": {
      category: "atomic.rmw",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 76,
    },
    "i64.atomic.rmw16.cmpxchg_u": {
      category: "atomic.rmw",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 77,
    },
    "i64.atomic.rmw32.cmpxchg_u": {
      category: "atomic.rmw",
      value: 254,
      return: ["i64"],
      parameter: ["addr", "i64", "i64"],
      immediate: [
        { name: "flags", type: "varuint32" },
        { name: "offset", type: "varuint32" },
      ],
      extendedOp: 78,
    },
  },
};

/*const description = JSON.parse(read("wasm.json", "caller relative")); // utilities.json("wasm.json");
//const type = Object.keys(description.type);
const _typeSet = new Set(type);
const isValidType = (v) => _typeSet.has(v);
const typeValue = _mapValues(description.type);
const _valueTypeSet = new Set(description.value_type);
const isValidValueType = (v) => _valueTypeSet.has(v);
const _blockTypeSet = new Set(description.block_type);
const isValidBlockType = (v) => _blockTypeSet.has(v);
const _refTypeSet = new Set(description.ref_type);
const isValidRefType = (v) => _refTypeSet.has(v);
const externalKindValue = _mapValues(description.external_kind);
const sections = Object.keys(description.section);
const sectionEncodingType = description.section[sections[0]].type;*/

function* opcodes(category = undefined) {
  for (let op in description.opcode)
    if (category !== undefined && description.opcode[op].category === category)
      yield { name: op, opcode: description.opcode[op] };
}
const memoryAccessInfo = (op) => {
  //                <-----------valueType----------->  <-------type-------><---------width-------->  <--sign-->
  const classify =
    /((?:i32)|(?:i64)|(?:f32)|(?:f64))\.((?:load)|(?:store))((?:8)|(?:16)|(?:32))?_?((?:s|u)?)/;
  const found = op.name.match(classify);
  const valueType = found[1];
  const type = found[2];
  const width = parseInt(found[3] ? found[3] : valueType.slice(1));
  const sign = (() => {
    switch (found[4]) {
      case "s":
        return "signed";
      case "u":
        return "unsigned";
      default:
        return "agnostic";
    }
  })();
  return { valueType, type, width, sign };
};

const constForValueType = (valueType) => {
  for (let op in description.opcode)
    if (op.endsWith(".const") && description.opcode[op]["return"] == valueType)
      return op;
  throw new Error(`Implementation problem: no const type for ${valueType}`);
};

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//utilities.js

const _environment =
  typeof process === "object" && typeof require === "function"
    ? "node"
    : typeof window === "object"
    ? "web"
    : typeof importScripts === "function"
    ? "worker"
    : "shell";

let _global =
  typeof global !== "object" ||
  !global ||
  global.Math !== Math ||
  global.Array !== Array
    ? typeof self !== "undefined"
      ? self
      : typeof window !== "undefined"
      ? window
      : typeof global !== "undefined"
      ? global
      : Function("return this")()
    : global;

const _eval = (x) => eval.call(null, x);

const _read = (filename) => {
  switch (_environment) {
    case "node":
      return read(filename);
    case "web": // fallthrough
    case "worker":
      let xhr = new XMLHttpRequest();
      xhr.open("GET", filename, /*async=*/ false);
      return xhr.responseText;
    case "shell":
      return read(filename);
  }
};

const _load = (filename) => {
  switch (_environment) {
    case "node": // fallthrough
    case "web": // fallthrough
    case "shell":
      return _eval(_read(filename));
    case "worker":
      return importScripts(filename);
  }
};

const _json = (filename) => {
  switch (_environment) {
    case "node": // fallthrough
    case "shell":
      return JSON.parse(_read(filename));
    case "web": // fallthrough
    case "worker":
      let xhr = new XMLHttpRequest();
      xhr.overrideMimeType("application/json");
      xhr.open("GET", filename, /*async=*/ false);
      return xhr.response;
  }
};

const _dump = (what, name, pad = "    ") => {
  const value = (v) => {
    try {
      return `"${v}"`;
    } catch (e) {
      return `Error: "${e.message}"`;
    }
  };
  let s = `${pad}${name} ${typeof what}: ${value(what)}`;
  for (let p in what) {
    s += `\n${pad}${pad}${p}: ${value(what[p])} ${typeof v}`;
    s += "\n" + _dump(what[p], p, pad + pad);
  }
  return s;
};

const toJavaScriptName = (name) => {
  const camelCase = name.replace(/([^a-z0-9].)/g, (c) => c[1].toUpperCase());
  const CamelCase = camelCase.charAt(0).toUpperCase() + camelCase.slice(1);
  return CamelCase;
};

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
