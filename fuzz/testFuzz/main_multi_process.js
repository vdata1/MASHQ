const { fork } = require('node:child_process');
const path = require('node:path');
const fs = require("node:fs");
const { readTestFiles, readSnippetFiles } = require('./fileUtils.js');

// Function to split the tests into chunks
function splitIntoChunks(arr, chunkSize) {
    const chunks = [];
    for (let i = 0; i < arr.length; i += chunkSize) {
        chunks.push(arr.slice(i, i + chunkSize));
    }
    return chunks;
}

// Main function to orchestrate fuzzing
function fuzzParallel(testsDir, snippetsDir, rounds, outputDir, numProcesses) {
    const tests = readTestFiles(testsDir);
    console.log(tests); 
    const snippets = readSnippetFiles(snippetsDir);

    // Split tests into chunks for each child process
    const testChunks = splitIntoChunks(tests, Math.ceil(tests.length / numProcesses));

    // Launch child processes
    testChunks.forEach((testChunk, index) => {
        const child = fork("./childFuzzer.js", [], {
               execArgv: ['--expose-gc', "--inspect", '--max-old-space-size=6096'], 
        });
        //(path.join(__dirname, 'childFuzzer.js'));

        child.send({ testChunk, snippets, rounds, outputDir, chunkId: index });

        // Listen for completion messages from the child process
        child.on('message', (message) => {
            if(message=="done"){
                console.log(`Child process ${index} completed:`, message);
                child.kill(); 
                if (global.gc) {
                    global.gc(); // run code with --expose-gc flag to trigger 
                } else {
                    console.warn('Garbage collection is not exposed');
                }
                
            }
            
        });

        // Handle child process exit
        child.on('exit', (code) => {
            if (code === 'done') {
                console.log(`Child process ${index} exited with code ${code}`);
                child.kill('0'); 
                if (global.gc) {
                    global.gc(); // run code with --expose-gc flag to trigger 
                } else {
                    console.warn('Garbage collection is not exposed');
                }                
            } else {
                console.log(`Child process ${index} Message: ${code}`);
              }
            
        });

        // Handle errors
        child.on('error', (err) => {
            console.error(`Error in child process ${index}:`, err);
            if (global.gc) {
                global.gc(); // run code with --expose-gc flag to trigger 
            } else {
                console.warn('Garbage collection is not exposed');
            }
            
        });
    });
    
    console.log("done"); 
}

// Call the main function with desired number of processes
const testsDir =  ['../../../test262/test']; //['../../../v8/mjsunit']; //['../../../test262/test'] //, '../../../v8/mjsunit', '../../../WebKit/JSTests/es6'] //, '../../../v8/mjsunit'];  //'../../../test262/test'; //'../../../v8/mjsunit'; //'/Users/vdata/Desktop/CISPA_projects/node-deno-bun/fuzz/testFuzz/testingTransfer'  //'../../../test262/test';       // Directory containing test files
const snippetsDir = '../../translation'; // Directory containing snippet examples
const rounds = 20;                // Number of fuzzing rounds
const outputDir = './output';     // Directory to store fuzzing results
const numProcesses = 1; //2900;  // Number of child processes to spawn

if (!fs.existsSync(outputDir))
    fs.mkdirSync(outputDir); 

fuzzParallel(testsDir, snippetsDir, rounds, outputDir, numProcesses);
console.log("done"); 
 
