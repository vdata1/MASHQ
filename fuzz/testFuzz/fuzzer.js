//const escodegen = require('escodegen');
const escodegen = require('astring');

const { readTestFiles, readSnippetFiles, createAST, readFileIfExists } = require('./fileUtils.js');
const { markLocation } = require('./markLocation.js');
const fs = require('node:fs');
const path = require('node:path');
const estraverse = require('estraverse');
//const HARNESS = "../../prep_tests/combined_harness_test262.js"

const runtimes = ['node', 'deno', 'bun'];

//const harnessFile = fs.readFileSync(HARNESS, 'utf-8');
//const harnessFunctions = createAST(harnessFile); 
//console.log("harnessFunctions gl: ", harnessFunctions);
// Clone AST to prevent modifying the original
function cloneAST(ast) {
    //console.log(ast);
    return structuredClone(ast); //JSON.parse(structuredClone(ast));//(JSON.stringify(ast));
}

// Helper function to check if a node is a require() statement
function isRequireStatement(node) {
    return node.type === 'VariableDeclaration' &&
           node.declarations &&
           node.declarations.some(decl => decl.init && decl.init.callee && decl.init.callee.name === 'require') /* || 
           node.type === 'VariableDeclaration' &&
           node.declarations &&
           node.declarations.some(decl => decl.init && decl.init.callee && decl.init.callee.name === 'import') ;
           */
}

// Helper function to collect all ImportDeclaration and require() statements
function collectImportAndRequireAndConstStatements(ast) {
    const imports = [];
    //let counter = 0; 
    estraverse.traverse(ast, {
        enter(node) {
            if (node.type === 'ImportDeclaration' || isRequireStatement(node)){ //|| (node.type === 'VariableDeclaration' && node.kind === 'const')) {
                //console.log("require/import/const detected...");
                imports.push(node);
                //counter ++; 
                //console.log(counter);
                this.remove(); 
            }
        }
    });

    return imports;
}

// Helper function to remove duplicate import/require statements
function deduplicateImportsAndConsts(importNodes) {
    const importMap = new Map();
    const uniqueImports = [];

    importNodes.forEach(node => {
        let importSource;
        
        if (node.type === 'ImportDeclaration') {
            importSource = node.source.value; // Extract the module path in import statement
        } else if (isRequireStatement(node)) {
            // Extract the module path from the require statement
            importSource = node.declarations[0].init.arguments[0].value;
        } /*else if(node.type === 'VariableDeclaration' && node.kind === 'const'){
            node.declarations.forEach(decl => {
                importSource = decl.id.name;
            });
        }*/

        if (!importMap.has(importSource)) {
            importMap.set(importSource, node);
            uniqueImports.push(node); // Add the unique import/require
        }
    });

    return uniqueImports;
}


function collectConstants(ast) {
    const constants = new Map();
    const otherStatements = [];

    // Traverse the AST to find all constant declarations
    estraverse.traverse(ast, {
        enter(node, parent) {
            if (node.type === 'VariableDeclaration' && node.kind === 'const') {
                // Collect the constants, ensuring no duplicates
                node.declarations.forEach(decl => {
                    const varName = decl.id.name;
                    if (!constants.has(varName)) {
                        constants.set(varName, node);
                    }
                });
                // Remove constant declarations from their original location
                return estraverse.VisitorOption.Remove;
            }
        }
    });

    // Collect the remaining statements
    ast.body.forEach(statement => {
        otherStatements.push(statement);
    });

    // Create a new AST with constants at the top
    const newAST = {
        type: 'Program',
        body: [
            ...Array.from(constants.values()),  // Move constants to the top
            ...otherStatements  // Followed by other statements
        ]
    };

    return newAST;
}

function injectSubtree(targetAST, subtree) {
    //console.log("TargetAST: ", targetAST); 
    //console.log("subTree: ", subtree); 
    //const originalAST = cloneAST(targetAST);
    let candidates = [];

    // Traverse the target AST and collect nodes that can hold statements (like BlockStatement)
    estraverse.traverse(targetAST, {
        enter: (node) => {
            //console.log("NODE: ", node);
            try{
                if (Array.isArray(node.body)) {
                    console.log("adding node...");
                    candidates.push(node);
                }
            }catch(err){
                console.log("skipping node");
            }
            
        }
    });

    // Pick a random candidate block for the injection
    const randomIndex = Math.floor(Math.random() * candidates.length);
    const randomNode = candidates[randomIndex];

    // Inject subtree at a random position within the selected block
    //const injectionIndex = Math.floor(Math.random() * (randomNode.body.length + 1));
    
    estraverse.traverse(targetAST, {
        enter: (node) => {
            //console.log("NODE: ", node);
            if(randomNode == node){
                node.body = [...node.body, ...subtree.body];
                return targetAST;
            }
        }
    });
    //console.log("change results: ", targetAST == originalAST);
    return targetAST;
}

//wrap modified ast by async Imedieatly Invoked Function Expression 
function wrapASTInAsyncIIFE(ast) {
    return {
        type: "Program",
        body: [
            {
                type: "ExpressionStatement",
                expression: {
                    type: "CallExpression",
                    callee: {
                        type: "ArrowFunctionExpression",
                        id: null,
                        generator: false,
                        async: true,
                        params: [],
                        body: {
                            type: "BlockStatement",
                            body: ast.body,
                        },
                    },
                    arguments: [],
                },
            },
        ],
        sourceType: "script",
    };
}

// Apply modifications based on flags and operations
function applyModifications(ast, runtime) {
    //console.log("AST: ", ast);
    const addedSnippets = []
    estraverse.replace(ast, {
        //enter(node, parent) {
        leave(node, parent) {    
             
            if (node._fuzzFlag) {
                const operation = node._fuzzFlag.operation;
                const injectedSnippet = operation!="skip" ? createAST(readFileIfExists(node._fuzzFlag.snippetAST[runtime])) : null;
                console.log("addedSnippets: ", addedSnippets);
                let uniqueImports;
                if(operation=="delete" || operation=="transfer"){
                    uniqueImports = deduplicateImportsAndConsts([...collectImportAndRequireAndConstStatements(ast)]);
                }else{
                    uniqueImports = deduplicateImportsAndConsts([...collectImportAndRequireAndConstStatements(ast), ...collectImportAndRequireAndConstStatements(injectedSnippet)]);
                } 
                if (operation === 'delete') {
                    try{
                        console.log("operation: ", operation);
                        //"return" to remove the subtree and stop the process. 
                        estraverse.VisitorOption.Remove;
                        /*
                            if(parent){
                                parent.remove();
                                //parent.body = null;
                                console.log("parent node removed...");
                            }else{
                                node.remove();
                                console.log("node removed..."); 
                            } 
                        */   
                    }catch(err){
                        console.log("Error in: ", operation, "\n\n", err);
                    }
                        
                }/*else if (operation === 'append' && !addedSnippets.includes(node._fuzzFlag.snippetAST[runtime])) {
                    try{
                        // Append the node with a snippet or another AST
                        ast.body = ast.body.concat(injectedSnippet.body);
                        addedSnippets.push(node._fuzzFlag.snippetAST[runtime]);
                    }catch(err){
                        console.log("Error in: ", operation, "\n\n", err);
                    }            
                } */ 
                else if(operation === 'transfer'){
                        console.log("operation: ", operation);
                        const mergeAST = cloneAST(node._fuzzFlag.mergeAST);
                        fuzzNodeIndex = parent.body.indexOf(node);
                        parent.body.splice(fuzzNodeIndex, 0, ...mergeAST.body)
                        console.log("fuzzNodeIndex: ", fuzzNodeIndex);
                        
                } else if (operation === 'inject_snippet' && addedSnippets.indexOf(node._fuzzFlag.snippetAST[runtime])==-1) {
                    console.log("Visited: ", operation);
                    try{
                        //console.log("node:  ", node);
                        console.log("snippetAST: ", node._fuzzFlag.snippetAST[runtime]);
                        fuzzNodeIndex = parent.body.indexOf(node);
                        parent.body.splice(fuzzNodeIndex, 0, ...injectedSnippet.body)
                        addedSnippets.push(node._fuzzFlag.snippetAST[runtime]);
                        console.log("fuzzNodeIndex: ", fuzzNodeIndex);
                    }catch(err){
                        console.log("Error in: ", operation, "\n\n", err);
                    }
                } else if(operation === 'inject_beggining' && addedSnippets.indexOf(node._fuzzFlag.snippetAST[runtime])==-1){
                    console.log("Visited: ", operation);
                    try{
                        const targetNode = ast.body[0]; 
                        if (targetNode && targetNode.body) {
                            targetNode.body.unshift(...injectedSnippet.body);
                            addedSnippets.push(node._fuzzFlag.snippetAST[runtime]); 
                        } else {
                            ast.body.unshift(...injectedSnippet.body);
                            addedSnippets.push(node._fuzzFlag.snippetAST[runtime]); 
                        }
                       // ast.body.unshift(...injectedSnippet.body);
                       //this.remove();
                    }catch(err){
                        console.log("Error in: ", operation, "\n\n", err);
                    }
                }else if(operation === 'inject_end' && addedSnippets.indexOf(node._fuzzFlag.snippetAST[runtime])==-1){ 
                    console.log("Visited: ", operation);
                    try{
                        ast.body.push(...injectedSnippet.body);
                        //this.remove();
                        addedSnippets.push(node._fuzzFlag.snippetAST[runtime]); 
                    }catch(err){
                        console.log("Error in: ", operation, "\n\n", err);
                    }
                } else{
                    console.log("operation skipped because there is no selected node..."); 
                    this.remove();
                }
                //console.log("added Snippets: ", addedSnippets);
                ast.body = ast.body.filter(node => node && node.type !== 'ImportDeclaration' && !isRequireStatement(node))//&& !(node.type === 'VariableDeclaration')); //&& node.kind === 'const'));
                ast.body.unshift(...uniqueImports);
            }
            
        }, 
    });  
    //output/round_2/node/nan_writeFile.js
   // ast = collectConstants(ast); 
    //wrap the ast by async IIFE 
    return wrapASTInAsyncIIFE(ast);
}

// Apply modifications to a cloned AST, preserving the original with flags
function performRoundWithFlags(ast, runtime){//snippetAST, modification, locations) {
    const clonedAST = cloneAST(ast);  // Clone the AST before applying changes
    return applyModifications(clonedAST, runtime);  // Apply changes on the clone
}

// Choose a modification and mark the AST with flags, including snippet and merge information
function chooseAndMarkModification(ast, snippets, additionalTestAST, round){//, operation=null) {
    //console.log("additional Snippet: ", addtionalSnippet); 

    const operations = ['delete', 'inject_snippet', 'transfer'];//, 'append'];
    const weights = [0.40, 0.10, 0.50]//, 0.2];
    const modification = weightedRandom(operations, weights);
    console.log("Selected modification: ", modification)//, "  Operation: ", operation); 
    
    // Randomly select a snippet from available snippets for inject/replace operations
    //const snippetAST =  snippets[Math.floor(Math.random() * snippets.length)];
    //console.log(snippetAST);
    
    // Mark the AST with the operation and relevant snippets
    try{
        /*
        if(modification === 'transfer'){
            let injectedCloneTest = cloneAST(additionalTestAST); 
            injectedCloneTest =  injectSnippet(injectedCloneTest, addtionalSnippet); 
            additionalTestAST = cloneAST(injectedCloneTest); 
         }
        */
         const markLocationResult = markLocation(ast, modification, snippets, round, additionalTestAST);//, addtionalSnippet=addtionalSnippet);
         let markLocationInfo = markLocationResult.nodeInfo
         const newAST = markLocationResult.ast;  
         console.log("Mark location info: ", markLocationInfo);
        // console.log("new AST: ", newAST);
         return {newAST, markLocationInfo};
    }catch(err){
        const x = {}
        console.log("Error:", err);
        return {ast, x};
         
    }
    
}

// Apply modifications across runtimes
function applyModificationsAcrossRuntimes(tests, snippets, round, outputDir) {
    let newASTs = []; 
    //console.log(tests);
    tests.forEach(test => {
        if(test.AST != null){
            //newASTs = []; 
            //const testAST = createAST(test.content);
            const testAST = test.AST; 
            const keys = Object.keys(snippets);
            const randomSnippet = Math.floor(Math.random(0, keys.length)*keys.length);//Math.random(0, keys.length); 
            //console.log("keyes: ", keys.length , "   randomsnippet: ", randomSnippet);
            const snippetName = keys[randomSnippet];
            //console.log("Selected snippet: ", snippetName);
            const availableSnippets = {
            "node": snippets[snippetName].node, //createAST(snippets[snippetName].node),
            "deno": snippets[snippetName].deno, //createAST(snippets[snippetName].deno),
            "bun" : snippets[snippetName].bun,  //createAST(snippets[snippetName].bun)
            };
            /*
            const randomAddiotionalSnippet =  Math.floor(Math.random(0, keys.length)*keys.length);
            //console.log("keyes: ", keys.length , "   additionalRandomSnippet: ", randomAddiotionalSnippet);
            
            const randomAddiotionalSnippetName = keys[randomAddiotionalSnippet];
            const addtionalSnippet = {
                "node": snippets[snippetName].node, //createAST(snippets[snippetName].node),
                "deno": snippets[snippetName].deno, //createAST(snippets[snippetName].deno),
                "bun" : snippets[snippetName].bun, //createAST(snippets[snippetName].bun)
            };
            */

            // Avoid additionalTestAST = testAST
            const testIndex = Object.keys(tests).indexOf(test); 
            let randIndix; 
            do {
                randIndix  = Math.floor(Math.random(0, Object.keys(tests).length) * Object.keys(tests).length); 
            } while (testIndex === randIndix);
              
            console.log("RandIndex: ", randIndix); 
             
            //console.log("content: ", tests[randIndix]);
            const additionalTestAST = tests[randIndix].AST;
            console.log("additionalTestAST apply: ", additionalTestAST);
            for(let i=0; i<6; i++){
                let breakFlag = 0;
                const modASTInfo = chooseAndMarkModification(testAST, availableSnippets, additionalTestAST, round);//, operation=null);
                const modAST = modASTInfo.newAST; 
                const markLocationInfo = modASTInfo.markLocationInfo;
                //console.log("markLocationInfo: ", markLocationInfo);
                const  modification = markLocationInfo.operation; 
                const clonedAST = cloneAST(modAST);
                
                //console.log("Modifications: ", modification);
                runtimes.forEach(runtime => {
                    const runtimeDir = path.join(outputDir, runtime);
                    if (!fs.existsSync(runtimeDir)) 
                        fs.mkdirSync(runtimeDir);
                    const modifiedAST = performRoundWithFlags(clonedAST, runtime);//, availableSnippets[runtime], modification, locations);
                    //console.log("Modifications: ", res.operation);
                    try{  
                        const code = escodegen.generate(modifiedAST);
                        const outputFilename = path.join(runtimeDir, `${path.basename(path.dirname(test.name))}_${path.basename(test.name, '.js')}_${modification}_${path.basename(snippetName, '.js')}.js`);
                        const comment = `// Round: ${round}, Runtime: ${runtime}, Test: ${test.name}, Snippet: ${snippetName}, additionalTestAST: ${tests[randIndix].name}, Modification: ${modification}\n`;
                        console.log("Comment: ", comment);
                        fs.writeFileSync(outputFilename, comment + code);
                        breakFlag = 1;  
                    }catch(err){
                        console.log("Error with generating code from AST: ", test.name)
                    }
                });   

                if(breakFlag){
                    console.log("Found a good mutation");
                    console.log("mod==new: ", modAST == clonedAST); 
                    newASTs.push({
                        name:  test.name, 
                        AST: modAST//clonedAST,
                    });
                    break;
                }else{
                    console.log("No mutation allowed escodegen to generate the code..."); 
                }
            }
        }

        else{
            console.warn(test.name, " has no content!"); 
        }
    });
    console.log("Next round ASTs: ", newASTs);
    console.log("Next round ASTs length: ", newASTs.length);
    return newASTs; 
}

function createASTs(testsDir){
    const testsATSs = readTestFiles(testsDir);
    return testsATSs
        .map(test => ({
            name: test.name,
            AST: createAST(test.content)
        }))
        .filter(test => test.AST);
}

// Main fuzzing function
function fuzz(testsDir, snippetsDir, rounds, outputDir) {

    let tests = createASTs(testsDir); //readTestFiles(testsDir);
    const snippets = readSnippetFiles(snippetsDir);
    let newTests = []; 
    let totalTests = tests.length;
    console.log("total tests: ", totalTests);

    for (let round = 1; round <= rounds; round++) {
        const roundDir = path.join(outputDir, `round_${round}`);
        if (!fs.existsSync(roundDir)) fs.mkdirSync(roundDir);
        //console.log("Number of tests: ", tests.length); 
        if(tests.length>0){
            newTests = applyModificationsAcrossRuntimes(tests, snippets, round, roundDir);
            console.log("Check tests: ", tests == newTests); 
            tests = newTests; 
            console.log("New round number of tests: ", tests.length); 
            totalTests += tests.length; 
            console.log("Total number of tests: ", totalTests);
            if (global.gc) {
                global.gc(); // run code with --expose-gc flag to trigger 
            } else {
                console.warn('Garbage collection is not exposed');
            }
            
        }else{
            console.log("Done, mo available ASTs to move to the next round..."); 
            break; 
        }
    }
}

// Helper functions
function weightedRandom(items, weights) {
    const cumulative = [];
    let sum = 0;
    weights.forEach(weight => {
        sum += weight;
        cumulative.push(sum);
    });

    const rand = Math.random() * sum;
    for (let i = 0; i < cumulative.length; i++) {
        if (rand < cumulative[i]) {
            return items[i];
        }
    }
}

module.exports = {
    chooseAndMarkModification, 
    applyModificationsAcrossRuntimes,    
    fuzz
};
