

# Node Deno Bun

## Fuzzer results 
### Platform-specific Data

| Platform  | Total   | Errors | Timeouts | Fatal Errors | Segmentation Faults | Panic |
|-----------|---------|--------|----------|--------------|---------------------|-------|
| Node | 208444  | 17242  | 68  | 34  | 0  | N/A  |
| Deno | 208444  | 20685  | 148  | 0  | 0  | 2  |
| Bun | 208444  | 10103  | 5  | 0  | 0  | 0  |

### Fuzzer: Symmetry in results

| Metric        | Count  |
|---------------|--------|
| All same | 168062 |
| All different | 22425 |
| Node deno | 455 |
| Node bun | 16665 |
| Deno bun | 837 |

### Fuzzer: Filtered results

<!--|Total|208444|
|:----|:----|
|Same output|184311|
|Same error|4019|
|Filtered out|8918|
|Different errors|10989|
|All 3 Different errors|49|
|Timeout|246|
|Panic|1|-->

|Field|Count|Descritpion|
|:----|:----|:----|
|Same output|184311|Same valid output in all 3|
|Same error|3913\*|Same error string in all 3|
|Timeout|216| |
|Panic|1| |
|Filtered out|9014\*|Files removed using filters (Same errors identified using filters)|
|Different outputs|10989|Atleast 1 different output|
|All 3 Different errors|49\*\*|All 3 completely different outputs (subset of Different outputs)|
|Total|208444|Total number of files|

\* 	 3913 is the number of Same errors identified during separation phase when files are separeated into Same output, Same error, 
	 Timeout and panic. These files have same error String in all 3 runtimes (SyntaxError, ReferenceError, TypeError, Test262Error).
	 Filters are applied to the remaining files (208444 - (184311 + 3913 + 216 + 1)) and this helped remove 9014 files. 
	 These files contain the same error but they do not contain the same error strings.   

\*\* 49 is included in 10989 so no need to consider it in total calculation



| |ReferenceError|SyntaxError|TypeError|Test262Error|Total|
|:----|:----|:----|:----|:----|:----|
|Same error|3639|16|444|20|4019|

|File:|Node error|Deno error|Bun error|All 3 Different|Valid node deno|Valid node bun|Valid deno bun|Valid Node only|Valid Deno only|Valid Bun only|Total files effected|
|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|
|Different errors|4835|8581|9045|49|237|296|552|5623|1621|1098|10989|

|File:|Node only timeout|Deno only timeout|Bun only timeout|Node and Deno timeout|Node and Bun timeout|Deno and Bun timeout|Total files effected|
|:----|:----|:----|:----|:----|:----|:----|:----|
|Timeout|65|0|0|0|0|0|65|

| |Node|Deno|Bun|Total files effected|
|:----|:----|:----|:----|:----|
|Crash|34|1|0|35|

### Filter: Fuzzer Round 1-10 counts

|Filter name|round_1| | |round_2| | |round_3| | |round_4| | |round_5| | |round_6| | |round_7| | |round_8| | |round_9| | |round_10| | |
|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|
| |node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|node.count|deno.count|bun.count|
|SyntaxError error error|1|1|1|1|0|0|2|1|1|3|2|2|5|5|2|10|9|8|12|12|10|8|8|6|11|10|8|14|14|13|
|SyntaxError SyntaxError error|1|0|0|1|0|0|2|1|1|3|2|2|5|4|1|10|8|7|12|10|8|8|6|4|11|9|8|14|13|12|
|Error  TypeError error|7|0|0|8|0|0|11|0|0|16|0|0|16|0|0|17|0|0|20|0|0|22|0|0|23|0|0|26|0|0|
|SyntaxError error SyntaxError|1|1|0|1|0|0|2|1|0|3|2|0|5|5|0|10|9|0|12|12|0|8|8|0|11|10|0|14|14|0|
|Test262Error Test262Error error|3|3|4|4|3|6|2|2|5|6|4|13|6|5|19|7|6|24|7|4|30|10|4|34|10|4|40|9|2|42|
|SyntaxError SyntaxError Syntax Error|1|0|0|1|0|0|2|1|0|3|2|0|5|4|0|10|8|0|12|10|0|8|6|0|11|9|0|14|13|0|
|subprocess killed|5|5|5|8|6|6|11|7|7|8|4|4|8|3|3|8|2|2|5|2|2|7|1|0|9|1|0|5|0|0|
|SyntaxError|1|0|0|1|0|0|2|1|0|3|2|0|5|4|0|10|8|0|12|10|0|8|6|0|11|9|0|14|13|0|
|TypeError|6|6|6|6|6|6|6|5|5|6|4|4|8|6|5|6|5|4|6|5|5|7|5|4|7|4|3|7|5|5|
|ReferenceError|0|0|0|2|2|2|3|3|3|3|3|3|6|2|1|10|2|2|9|2|2|13|2|2|14|4|3|16|3|1|
|Test262Error|7|6|0|6|5|0|7|6|0|13|9|0|12|9|0|12|9|0|13|6|0|14|6|0|12|6|0|13|3|0|
|Cannot use import|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|escape characters cannot be escaped|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid destructuring|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid left hand|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid left hand, module-parsed, Invalid target|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Lexical declaration cannot appear in a single-statement context|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Malformed arrow function|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Require a function name|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot use reserved word|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|strict mode reserved word|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|super keyword unexpected|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid tagged template|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unary operator used immediately before exponentiation expression|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected end of input|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected string|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected token |0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Yield expression cannot be used|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|arguments not allowed|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot use a declaration in a single-statement context|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Keyword must not contain escaped characters|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
| for-await-of loop variable declaration may not have an initializer|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
| Generators can only be declared at the top level or inside a block|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Getter must not have any formal parameters|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Illegal await-expression|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Illegal break|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Illegal continue|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid left hand, Invalid left-hand, Invalid target|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid shorthand|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|disallowed keyword|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Missing catch or finally after try|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|not a valid identifier name|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Private field|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Private fields|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid regular expression|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected strict mode reserved word|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Rest element must be last element|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Classes may not have a static property named 'prototype'|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|In strict mode code, functions can only be declared at top level or inside a block|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid tagged template|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|await is only valid in async functions and the top level bodies of modules|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Undefined label|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected eval |0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected identifier|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|1|1|0|2|1|0|2|1|0|1|0|0|0|0|0|
|Unexpected number|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected string|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unexpected token |0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot find package|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|for-in loop variable declaration may not have an initializer|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot declare function named 'await' in an async function|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Unterminated regexp literal|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|unexpected token, Syntax Error|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Address in use|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Invalid or unexpected token|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot use outside a module, Invalid destructuring|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|
|Cannot use outside a module, Invalid left-hand|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|


### Filter: Fuzz/Test262 counts 

|Filter name|Fuzz| | |Test 262| | |
|:----|:----|:----|:----|:----|:----|:----|
| |node.count|deno.count|bun.count|node.count|deno.count|bun.count|
|SyntaxError error error|71|32|32|3367|2868|2852|
|SyntaxError SyntaxError error|71|10|10|3367|1809|1800|
|Error  TypeError error|819|210|210|1027|99|85|
|SyntaxError error SyntaxError|71|32|0|3367|2868|71|
|Test262Error Test262Error error|453|230|755|407|280|4207|
|SyntaxError SyntaxError Syntax Error|71|10|0|3367|1809|47|
|subprocess killed|16582|16299|16251|0|0|0|
|SyntaxError|71|10|0|3367|1809|48|
|TypeError|1447|477|350|273|226|170|
|ReferenceError|3713|3713|3543|3384|3082|2921|
|Test262Error|759|404|20|993|326|22|
|Cannot use import|20|0|0|146|21|21|
|escape characters cannot be escaped|0|0|0|143|70|4|
|Invalid destructuring|0|0|0|104|98|5|
|Invalid left hand|0|0|0|434|193|41|
|Invalid left hand, module-parsed, Invalid target|0|0|0|434|193|150|
|Lexical declaration cannot appear in a single-statement context|0|0|0|18|17|17|
|Malformed arrow function|0|0|0|2|2|1|
|Require a function name|0|0|0|5|5|5|
|Cannot use reserved word|0|0|0|56|27|15|
|strict mode reserved word|0|0|0|33|12|8|
|super keyword unexpected|0|0|0|81|1|1|
|Invalid tagged template|0|0|0|8|4|4|
|Unary operator used immediately before exponentiation expression|0|0|0|7|7|7|
|Unexpected end of input|0|0|0|4|3|1|
|Unexpected string|0|0|0|29|6|6|
|Unexpected token |0|0|0|512|336|157|
|Yield expression cannot be used|0|0|0|6|5|5|
|arguments not allowed|0|0|0|30|30|30|
|Cannot use a declaration in a single-statement context|0|0|0|30|25|25|
|Keyword must not contain escaped characters|0|0|0|72|72|63|
| for-await-of loop variable declaration may not have an initializer|0|0|0|43|43|6|
| Generators can only be declared at the top level or inside a block|0|0|0|4|4|4|
|Getter must not have any formal parameters|0|0|0|1|1|1|
|Illegal await-expression|10|10|0|43|43|2|
|Illegal break|0|0|0|6|6|6|
|Illegal continue|10|10|0|5|5|4|
|Invalid left hand, Invalid left-hand, Invalid target|0|0|0|241|241|201|
|Invalid shorthand|0|0|0|1|1|1|
|disallowed keyword|0|0|0|6|6|6|
|Missing catch or finally after try|0|0|0|3|3|3|
|not a valid identifier name|0|0|0|4|3|3|
|Private field|0|0|0|160|160|159|
|Private fields|0|0|0|96|96|96|
|Invalid regular expression|0|0|0|351|351|2|
|Unexpected strict mode reserved word|0|0|0|29|28|2|
|Rest element must be last element|0|0|0|98|98|98|
|Classes may not have a static property named 'prototype'|0|0|0|8|8|8|
|In strict mode code, functions can only be declared at top level or inside a block|0|0|0|58|57|14|
|Invalid tagged template|0|0|0|4|4|4|
|await is only valid in async functions and the top level bodies of modules|0|0|0|2|2|2|
|Undefined label|0|0|0|23|23|23|
|Unexpected eval |0|0|0|10|10|4|
|Unexpected identifier|0|0|0|18|13|13|
|Unexpected number|0|0|0|4|3|2|
|Unexpected string|0|0|0|23|21|21|
|Unexpected token |0|0|0|159|122|54|
|Cannot find package|0|0|0|19|19|19|
|for-in loop variable declaration may not have an initializer|0|0|0|8|4|2|
|Cannot declare function named 'await' in an async function|0|0|0|8|3|1|
|Unterminated regexp literal|0|0|0|21|21|21|
|unexpected token, Syntax Error|0|0|0|71|52|52|
|Address in use|11124|9635|8804|0|0|0|
|Invalid or unexpected token|0|0|0|66|66|31|
|Cannot use outside a module, Invalid destructuring|20|0|0|125|4|4|
|Cannot use outside a module, Invalid left-hand|20|0|0|125|9|9|



<!--|Filter name|node.count|deno.count|bun.count|
|:----|:----|:----|:----|
|SyntaxError error error|71|32|32|
|SyntaxError SyntaxError error|71|10|10|
|error TypeError error|17242|689|560|
|SyntaxError error SyntaxError|71|32|0|
|Test262Error Test262Error error|453|230|755|
|SyntaxError SyntaxError Syntax Error|71|10|0|
|subprocess killed|16582|16299|16251|
|SyntaxError|71|10|0|
|TypeError|1447|477|350|
|ReferenceError|3713|3713|3543|
|Test262Error|759|404|20|
|Address in use|11124|9635|8804|
|Illegal await-expression|10|10|0|
|Illegal continue|10|10|0|
|Cannot use|60|0|0|
|escape characters cannot be escaped|0|0|0|
|Invalid destructuring|0|0|0|
|Invalid left hand|0|0|0|
|Invalid left hand, module-parsed, Invalid target|0|0|0|
|Lexical declaration cannot appear in a single-statement context|0|0|0|
|Malformed arrow function|0|0|0|
|Require a function name|0|0|0|
|Cannot use reserved word|0|0|0|
|strict mode reserved word|0|0|0|
|super keyword unexpected|0|0|0|
|Invalid tagged template|0|0|0|
|Unary operator used immediately before exponentiation expression|0|0|0|
|Unexpected end of input|0|0|0|
|Unexpected string|0|0|0|
|Unexpected token |0|0|0|
|Yield expression cannot be used|0|0|0|
|arguments not allowed|0|0|0|
|Cannot use a declaration in a single-statement context|0|0|0|
|Keyword must not contain escaped characters|0|0|0|
| for-await-of loop variable declaration may not have an initializer|0|0|0|
| Generators can only be declared at the top level or inside a block|0|0|0|
|Getter must not have any formal parameters|0|0|0|
|Illegal break|0|0|0|
|Invalid left hand, Invalid left-hand, Invalid target|0|0|0|
|Invalid shorthand|0|0|0|
|disallowed keyword|0|0|0|
|Missing catch or finally after try|0|0|0|
|not a valid identifier name|0|0|0|
|Private field|0|0|0|
|Private fields|0|0|0|
|Invalid regular expression|0|0|0|
|Unexpected strict mode reserved word|0|0|0|
|Rest element must be last element|0|0|0|
|Classes may not have a static property named 'prototype'|0|0|0|
|In strict mode code, functions can only be declared at top level or inside a block|0|0|0|
|Invalid tagged template|0|0|0|
|await is only valid in async functions and the top level bodies of modules|0|0|0|
|Undefined label|0|0|0|
|Unexpected eval |0|0|0|
|Unexpected identifier|0|0|0|
|Unexpected number|0|0|0|
|Unexpected string|0|0|0|
|Unexpected token |0|0|0|
|Module not found|0|0|0|
|Cannot find package|0|0|0|
|for-in loop variable declaration may not have an initializer|0|0|0|
|Cannot declare function named 'await' in an async function|0|0|0|
|Unterminated regexp literal|0|0|0|
|unexpected token, Syntax Error|0|0|0|
|Invalid or unexpected token|0|0|0|-->


<!--|filters|node.count|deno.count|bun.count|
|:----|:----|:----|:----|
|low_level_filter_1|89|49|42|
|low_level_filter_2|89|27|20|
|low_level_filter_3|17242|800|640|
|low_level_filter_4|89|49|17|
|low_level_filter_5|89|27|0|
|low_level_filter_6|453|230|755|
|low_level_filter_7|89|27|0|
|low_level_filter_8|89|27|20|
|low_level_filter_9|16582|16299|16251|
|filter_1|60|0|0|
|filter_2|0|0|0|
|filter_3|0|0|0|
|filter_4|0|0|0|
|filter_5|0|0|0|
|filter_6|0|0|0|
|filter_7|0|0|0|
|filter_8|0|0|0|
|filter_9|0|0|0|
|filter_10|0|0|0|
|filter_11|0|0|0|
|filter_12|0|0|0|
|filter_13|0|0|0|
|filter_14|0|0|0|
|filter_15|0|0|0|
|filter_16|0|0|0|
|filter_17|0|0|0|
|filter_18|0|0|0|
|filter_19|0|0|0|
|filter_20|0|0|0|
|filter_21|0|0|0|
|filter_22|0|0|0|
|filter_23|0|0|0|
|filter_24|0|0|0|
|filter_25|10|10|0|
|filter_26|0|0|0|
|filter_27|10|10|0|
|filter_28|0|0|0|
|filter_29|0|0|0|
|filter_30|0|0|0|
|filter_31|0|0|0|
|filter_32|0|0|0|
|filter_33|0|0|0|
|filter_34|0|0|0|
|filter_35|0|0|0|
|filter_36|0|0|0|
|filter_37|0|0|0|
|filter_38|0|0|0|
|filter_39|0|0|0|
|filter_40|0|0|0|
|filter_41|0|0|0|
|filter_42|0|0|0|
|filter_43|0|0|0|
|filter_44|0|0|0|
|filter_45|0|0|0|
|filter_46|0|0|0|
|filter_47|0|0|0|
|filter_48|0|0|0|
|filter_49|0|0|0|
|filter_50|0|0|0|
|filter_51|0|0|0|
|filter_52|0|0|0|
|filter_53|0|0|0|
|filter_54|11124|9635|8804|
|filter_55|0|0|0|-->




# Reported Bugs
Confirmed: 9 (new) + 3 (old) 
|Target Runtime|Bug type|OS|Technique|Bug title|Bug URL|Submission Date|Resolved Date|Status|Confirmed|
|:----|:----|:----|:----|:----|:----|:----|:----|:----|:----|
|Deno|Code|Both|v8 without fuzzer|Deno has panicked when prototype.__defineSetter__ used on built-in objects|https://github.com/denoland/deno_core/issues/744|14-05-2024| |Open|✓|
|Deno|Code|Both|v8 without fuzzer|Deno has panicked when defineProperty used on Deno "Object"|https://github.com/denoland/deno_core/issues/743|14-05-2024|21-05-2024|Closed|✓|
|Deno|Code|Both|v8 without fuzzer|Deno has panicked while using defineProperty on "Object"|https://github.com/denoland/deno_core/issues/742|14-05-2024|21-05-2024|Closed|✓|
|Bun|Code|Both|v8 without fuzzer|Thread 5908 panic: reached unreachable code while using 'Bun.Transpiler.transform|https://github.com/oven-sh/bun/issues/11444|29-05-2024| |Open|on old version|
|Bun|Code|Both|test262 without fuzzer|Bun panic caused by Segmentation fault.|https://github.com/oven-sh/bun/issues/12039|21-06-2024|23-06-2024|Closed|✓|
|Bun|Code|Both|test262 without fuzzer|Transpiler not visiting scopes in with argument of import expression causes assertion failure|https://github.com/oven-sh/bun/issues/12123|24-06-2024|17-07-2024|Closed|✓|
|Deno|Code|Both| |Deno runtime stuck in endless loop while running Array.prototype[0]=0;|https://github.com/denoland/deno/issues/24358|27-06-2024|27-06-2024|Closed|✓|
| ̶D̶e̶n̶o̶| ̶C̶o̶d̶e̶|Both| ̶A̶P̶I̶ ̶r̶e̶l̶a̶t̶e̶d̶| ̶D̶e̶n̶o̶ ̶p̶a̶n̶i̶c̶ ̶w̶h̶i̶l̶e̶ ̶u̶s̶i̶n̶g̶ ̶D̶e̶n̶o̶.̶c̶o̶n̶n̶e̶c̶t̶T̶l̶s̶(̶)̶ ̶i̶n̶ ̶(̶a̶s̶y̶n̶c̶ ̶f̶u̶n̶c̶t̶i̶o̶n̶(̶)̶{̶}̶(̶)̶)̶| ̶h̶t̶t̶p̶s̶:̶/̶/̶g̶i̶t̶h̶u̶b̶.̶c̶o̶m̶/̶d̶e̶n̶o̶l̶a̶n̶d̶/̶d̶e̶n̶o̶/̶i̶s̶s̶u̶e̶s̶/̶2̶4̶3̶8̶9̶| ̶0̶2̶-̶0̶7̶-̶2̶0̶2̶4̶| ̶0̶2̶-̶0̶7̶-̶2̶0̶2̶4̶| ̶C̶l̶o̶s̶e̶d̶| ̶a̶l̶r̶e̶a̶d̶y̶ ̶d̶i̶s̶c̶o̶v̶e̶r̶e̶d̶|
|Deno|Code|Both|test262 without fuzzer|Deno runtime stuck while Object.defineProperty|https://github.com/denoland/deno/issues/24431|04-07-2024|04-07-2024|Closed|on old canary version|
|Bun|Code|MacOS|API related|Bun panic by Bun.CryptoHasher.update|https://github.com/oven-sh/bun/issues/12597|16-07-2024|16-07-2024|Closed|✓|
|Deno |Code|Both|API related|Deno APIs missing in Deno runtime|https://github.com/denoland/deno/issues/24638|18-07-2024|18-07-2024|Closed|works with "--unstable" flag|
|Deno |Code|Both|Fuzz|Deno panic while calling fetch Result::unwrap() after Object.defineProperty|https://github.com/denoland/deno/issues/24784|29-07-2024| |Open|✓|
|Deno |Code|Both|Fuzz|this is undefined |https://github.com/denoland/deno/issues/24861|03-08-2024|05-08-2024|Closed| |
|Node|Code|Both|Fuzz|FATAL ERROR v8::FromJust Maybe value is Nothing|https://github.com/nodejs/node/issues/54186#issuecomment-2267616435|03-08-2024|05-11-2024|Closed|✓|
|Bun|Code|Both|Fuzz|this have different values in different scopes|https://github.com/oven-sh/bun/issues/13050#issuecomment-2266874688|03-08-2024|08-08-2024|Closed| |
|Bun|Code|Both|test262 without fuzzer|Unexpected behaviour in Bun's static analysis|https://github.com/oven-sh/bun/issues/13992|17-09-2024| |Open|✓|
|Deno|Documentation|Both|test262 without fuzzer|javascript.builtins.Intl.Locale.getWeekInfo - Deno uses a non-standard name |https://github.com/mdn/browser-compat-data/issues/24459|17-09-2024|04-03-2025|Closed|✓|
|Deno|Documentation|Both|test262 without fuzzer|javascript.builtins.Intl.DurationFormat - Currently supported by Deno|https://github.com/mdn/browser-compat-data/issues/24460|17-09-2024|04-03-2025|Closed|✓|
|Bun|Code|Both|test262 without fuzzer|Runtime DCE leads to overridden new WeakMap([]); not being called|https://github.com/oven-sh/bun/issues/14217|27-09-2024| |Open|✓|
|Bun|Javascript Core Engine Bug|Both|test262 without fuzzer|Cannot fill all elemnts of Int8Array using Int8Array.fill|https://github.com/oven-sh/bun/issues/14247|30-09-2024| |Open|✓|
|Bun|Code|Both|test262 without fuzzer|Strict mode is not working in block scope|https://github.com/oven-sh/bun/issues/14273|01-10-2024| |Open|✓|
|Bun|Code|Both|test262 without fuzzer|Intl.NumberFormat.resolvedOptions() gives differnet value than NodeJs and Deno|https://github.com/oven-sh/bun/issues/14712|21-10-2024| |Open|✓|
|Bun|Code|Both|test262 without fuzzer|The region is not changed in Intl.Locale|https://github.com/oven-sh/bun/issues/14713|21-10-2024| |Open|✓|
|Node|Code|Both|test262 without fuzzer|Some currencies are not available in Intl.supportedValuesOf("currency")|https://github.com/nodejs/node/issues/55483|21-10-2024|21-10-2024|Closed| |
|Bun|Code|Both|test262 without fuzzer|Accessing functions from outside blockStatement|https://github.com/oven-sh/bun/issues/14715|21-10-2024| |Open|✓|
|Bun|Code|Both|Stage|Handling an invalid regualr expression |https://github.com/oven-sh/bun/issues/15219|18-11-2024| |Open|✓|
|Node|Code|Both| |FATAL ERROR: v8::ToLocalChecked Empty MaybeLocal|https://github.com/nodejs/node/issues/55932|20-11-2024|05-06-2025|Closed| |
|Bun|Code|Both|test262 without fuzzer|Bun prints Unicode \uFEFF differently from Node,Deno|https://github.com/oven-sh/bun/issues/15492|29-11-2024| |Open|✓|
|Deno|CLI|Both| |Deno cli could not initialize cache database|https://github.com/denoland/deno/issues/27283|18-12-2024| |Open|✓|
|Bun|Code|Both|test262 without fuzzer|Bun does not throw error|https://github.com/oven-sh/bun/issues/15848|18-12-2024| |Open| |
|Node|Code|Both|Fuzz|FATAL ERROR: v8::ToLocalChecked Empty MaybeLocal #56531|https://github.com/nodejs/node/issues/56531|09-01-2025| |Open| |
|Deno|Code|Windows|test262 with Fuzzer|Deno panic while using Object.prototype.set and Deno.Command together|https://github.com/denoland/deno/issues/27720|18-01-2025| |Open|✓|
|Deno|Code|Both|webkit without fuzzing|Deno panic due to call Option::unwrap() on a None value|https://github.com/denoland/deno/issues/27736|20-01-2025|27-01-2025|Closed|✓|
|Deno|Code|Both|test262 with Fuzzer|use Object.defineProperty to tamper Uint8Array.|https://github.com/denoland/deno/issues/27746|20-01-2025| |Open| |
|Bun|Code|Both|v8 with fuzzer|Bun does not provide output when RegExp["$`"] is used|https://github.com/oven-sh/bun/issues/16797|27-01-2025|27-01-2025|Closed|✓|
|Bun|Code|Both|v8 with fuzzer|RegExp global properties differ from V8 runtimes|https://github.com/oven-sh/bun/issues/16798|27-01-2025|07-03-2025|Closed|✓|
|Bun|Code|Both|v8 with fuzzer|Bun does not provide last matched string when using RegExp["$&"]|https://github.com/oven-sh/bun/issues/17978|07-03-2025|10-03-2025|Closed|✓|
|Bun|Code|Both|v8 with fuzzer|Segmentation fault at address 0x5|https://github.com/oven-sh/bun/issues/18004|09-03-2025| |Open| |
|Deno|Code|Both|v8 with fuzzer|Deno panic at deno_core-0.340.0 due to Uncaught RangeError: Maximum call stack size exceeded|https://github.com/denoland/deno/issues/28436|09-03-2025| |Open|✓|
|Bun|Code|Both|v8 with fuzzer|RegExp unicode mode differs from V8 runtimes|https://github.com/oven-sh/bun/issues/18018|09-03-2025|21-03-2025|Closed|✓|
|Bun|Code|Windows|v8 with fuzzer|Bun.$`pwd`.text() does not work as expected when used with process.chdir()|https://github.com/oven-sh/bun/issues/18331|20-03-2025| |Open| |
|Node|Code|Both|v8 with fuzzer|Error in converting circular structure to JSON in Node|https://github.com/nodejs/node/issues/57566|20-03-2025|20-03-2025|Closed| |
|Bun|Code|Both|v8 with fuzzer|Bun does not throw SyntaxError when 'use strict' used inside a function with non-simple parameters|https://github.com/oven-sh/bun/issues/18333|20-03-2025| |Open| |
|Node|Documentation|Both|v8 with fuzzer|Error.captureStackTrace() - Currently not supported by Node.js|https://github.com/mdn/browser-compat-data/issues/26271|21-03-2025|24-03-2025|Closed|✓|
|Deno|Code|Both|v8 with fuzzer|RegExp unicode mode differs from Bun runtime|https://github.com/denoland/deno/issues/28587|21-03-2025|27-03-2025|Closed| |
|Bun|Code|Both|v8 with fuzzer|RegExp unicode mode JIT treats escaped surrogate followed by literal surrogate as surrogate pair|https://github.com/oven-sh/bun/issues/18540|27-03-2025|12-05-2025|Closed|✓|
|Bun|Code|MacOS|v8 with fuzzer|Seg fault at address 0x5 |https://github.com/oven-sh/bun/issues/19650|14-05-2025| |Open|✓|
|Deno|Code|Both|v8 with fuzzer|Deno panic due to calling Option::unwrap() on a None value|https://github.com/denoland/deno/issues/29312|15-05-2025| |Open|✓|
|Deno|Code|Both|v8 with fuzzer|Deno panic when customizing Error.prepareStackTrace|https://github.com/denoland/deno/issues/29409|21-05-2025| |Open|✓|
|Bun|Code|Both|v8 with fuzzer|String object with Symbol.isConcatSpreadable behaves differently in Bun vs Node/Deno|https://github.com/oven-sh/bun/issues/20077|30-05-2025| |Open|✓|
|Deno|Code|Both|v8 with fuzzer|TypeError: when using fetch in Deno but not in Bun|https://github.com/denoland/deno/issues/29535|30-05-2025|30-05-2025|Closed| |
|Bun|Code|Both|v8 with fuzzer|Symbol.replace on Object.prototype not invoked by String.prototype.replace in Bun|https://github.com/oven-sh/bun/issues/20078|30-05-2025|31-05-2025|Closed| |
|Deno|Code|Both|test262 with Fuzzer|regExp.test behaves differently in Deno|https://github.com/denoland/deno/issues/29537|30-05-2025|30-05-2025|Closed| |
|Bun|Code|Both|test262 with Fuzzer|Intl.DateTimeFormat options object with getter keys causes TypeError in Bun but works in Node and Deno|https://github.com/oven-sh/bun/issues/20083|30-05-2025| |Open|✓|
|Bun|Code|Windows|test262 with Fuzzer|Bun panic on hasOwnProperty call with custom valueOf and async Bun.$ call|https://github.com/oven-sh/bun/issues/20344|12-06-2025| |Open|✓|
|Bun|Code|Both|test262 with Fuzzer|Overriding Array.prototype[Symbol.iterator] with typed array logic causes RangeError in Bun|https://github.com/oven-sh/bun/issues/20345|12-06-2025| |Open|✓|
|Deno|Code|Both|test262 with Fuzzer|Deno panic when Array.prototype["0"] is defined with a getter and Deno.readTextFile is called|https://github.com/denoland/deno/issues/29824|20-06-2025| |Open|✓|
|Bun|Code|Windows|test262 with Fuzzer|Defining Object.prototype["1"] setter causes Bun to panic during env access|https://github.com/oven-sh/bun/issues/20514|20-06-2025| |Open|✓|
|Bun|Code|Both|test262 with Fuzzer|Intl.DateTimeFormat returns different dayPeriod results on Windows vs MacOS|https://github.com/oven-sh/bun/issues/20634|25-06-2025| |Open| |
|Bun|Code|Both|test262 with Fuzzer|Intl.getCanonicalLocales returns different results on Windows vs MacOS|https://github.com/oven-sh/bun/issues/20635|25-06-2025| |Open| |
|Bun|Code|Both|test262 with Fuzzer|Different output when Node.js/npm support is used|https://github.com/oven-sh/bun/issues/20636|25-06-2025| |Open| |
|Node|Code|Both|test262 with Fuzzer|RegExp.prototype.test produces inconsistent results in Node.js vs Chrome|https://github.com/nodejs/node/issues/58905|30-06-2025| |Open| |




# TEST SUITE VERSIONS


## V8

 https://chromium.googlesource.com/v8/v8.git/+/refs/heads/main/test/mjsunit/

 commit version: https://chromium.googlesource.com/v8/v8.git/+/d8147eb98cacfc65a802b94b3c0dc9cf88f546ab


## TEST262

 https://github.com/tc39/test262/commit/8296db887368bbffa3379f995a1e628ddbe8421f

## WEBKIT

 https://github.com/WebKit/WebKit/commit/36f65ab58b5d911990709e76c838479f0fd6a7fb

 Commit 36f65ab













# Crashes

<!--|Test Set|Total| |Unique after minimisation| |
|:----|:----|:----|:----|:----|
| |Deno|Bun|Deno|Bun|
|v8|3|1|3|1|
|test262|0|196|0|3|-->

|Test Set|Crash| |Fatal Error|Unique crash after minimisation| |
|:----|:----|:----|:----|:----|:----|
| |Deno|Bun|Node|Deno|Bun|
|v8|3|1|1|3|1|
|test262|0|196|3|0|3|




<!--# API adaptations

|Runtime|API|Adaptable to| | |Notes|
|:----|:----|:----|:----|:----|:----|
| | |Node|Deno |Bun| |
|Bun|Bun.connect|Yes|Yes| | |
|Bun|Bun.cryptohasher|Yes|Yes| | |
|Bun|Bun.deepEquals|Yes|Yes| | |
|Bun|Bun.deflateSync|Yes|Yes| | |
|Bun|Bun.file|Yes|Yes| | |
|Bun|Bun.gunzipSync|Yes|Yes| | |
|Bun|Bun.gzipSync|Yes|Yes| | |
|Bun|Bun.inflateSync|Yes|Yes| | |
|Bun|Bun.inspect|Yes|Yes| | |
|Bun|Bun.listen|Yes|Yes| | |
|Bun|Bun.nanoseconds|Yes|Yes| | |
|Bun|Bun.password.hash|Yes| | | |
|Bun|Bun.peek|Yes|Yes| | |
|Bun|Bun.serve|Yes|Yes| | |
|Bun|Bun.sleep|Yes|Yes| | |
|Bun|Bun.stringWidth|Yes|Yes| | |
|Bun|Bun.which|Yes| | | |
|Deno|Deno.addSignalListener|Yes| |Yes| |
|Deno|Deno.bench|Yes| | | |
|Deno|Deno.chdir|Yes| |Yes| |
|Deno|Deno.chmod|Yes| |Yes|Deno: Not on windows|
|Deno|Deno.chown| | | |Deno: Not on windows|
|Deno|Deno.consoleSize|Yes| |Yes| |
|Deno|Deno.copyfile|Yes| |Yes| |
|Deno|Deno.copyFIleSync|Yes| |Yes| |
|Deno|Deno.create|Yes| |Yes| |
|Deno|Deno.createSync|Yes| |Yes| |
|Deno|Deno.cwd|Yes| |Yes| |
|Deno|Deno.execPath|Yes| |Yes| |
|Deno|Deno.exit|Yes| |Yes| |
|Deno|Deno.fdatasync| | | | |
|Deno|Deno.inspect|Yes| |Yes| |
|Deno|Deno.loadavg|Yes| |Yes| |
|Deno|Deno.lstat|Yes| |Yes| |
|Deno|Deno.lstatSync|Yes| |Yes| |
|Deno|Deno.makeTempDir|Yes| |Yes| |
|Deno|Deno.listenDatagram|Yes| |Yes|Deno: use --unstable flag
|Deno|Deno.link|Yes| |Yes|Deno: Not on windows| -->


# FILTERS

  Filters can be found in results/test262_separated_results/README.md


