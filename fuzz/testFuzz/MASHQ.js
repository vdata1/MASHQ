const { fork } = require('node:child_process');
const path = require('node:path');
const fs = require("node:fs");
const { readTestFiles, readSnippetFiles } = require('./fileUtils.js');
const args = require('node:process').argv.slice(2);

// Function to split the tests into chunks
function splitIntoChunks(arr, chunkSize) {
    const chunks = [];
    for (let i = 0; i < arr.length; i += chunkSize) {
        chunks.push(arr.slice(i, i + chunkSize));
    }
    return chunks;
}

// Main function to orchestrate fuzzing
function fuzzParallel(testsDir, snippetsDir, rounds, outputDir, numProcesses, numTests) {
    const tests = readTestFiles(testsDir,numTests);
    console.log(tests); 
    const snippets = readSnippetFiles(snippetsDir);
    console.log(snippets.length, " snippet files found");
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

// Parse command line arguments with flags and defaults

function parseArgs(args) {
    const options = {
        testsDir: ['../../../test262/test'],
        snippetsDir: '../../translation',
        rounds: 20,
        outputDir: './output',
        numProcesses: 1,
        numTests: 'all' // Default value for number of tests
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '-h':
            case '--help':
                console.log(`
Usage: node MASHQ.js [options]

Options:
  -t <dirs>      Comma-separated list of test directories (default: "../../../test262/test")
  -s <dir>       Snippets directory (default: "../../translation")
  -r <rounds>    Number of rounds (default: 20)
  -o <dir>       Output directory (default: "./output")
  -n <num>       Number of processes (default: 1)
  -N <num|all>   Number of tests per process or 'all' (default: all)
  -h, --help     Show this help message
`);
                process.exit(0);
                break;
            case '-t':
                options.testsDir = args[i + 1] ? args[i + 1].split(',') : options.testsDir;
                i++;
                break;
            case '-r':
                options.rounds = args[i + 1] ? Number(args[i + 1]) : options.rounds;
                i++;
                break;
            case '-n':
                options.numProcesses = args[i + 1] ? Number(args[i + 1]) : options.numProcesses;
                i++;
                break;
            case '-s':
                options.snippetsDir = args[i + 1] || options.snippetsDir;
                i++;
                break;
            case '-o':
                options.outputDir = args[i + 1] || options.outputDir;
                i++;
                break;
            case '-N':
                options.numTests = args[i + 1] ? (args[i + 1] === 'all' ? 'all' : Number(args[i + 1])) : options.numTests;
                i++;
                break;
        }
    }
    return options;
}

const { testsDir, snippetsDir, rounds, outputDir, numProcesses, numTests } = parseArgs(args);

// Usage: node main_multi_process.js -t "../../../test262/test,../../../v8/mjsunit" -s "../../translation" -r 20 -o "./output" -n 4 -N 100



if (!fs.existsSync(outputDir))
    fs.mkdirSync(outputDir); 

console.log(`Starting fuzzing with ${numProcesses} processes, ${rounds} rounds, and ${numTests} tests per process.`);
fuzzParallel(testsDir, snippetsDir, rounds, outputDir, numProcesses, numTests);
console.log("done"); 
 
//return null; 