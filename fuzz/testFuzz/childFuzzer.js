const { createAST } = require('./fileUtils.js');
const { chooseAndMarkModification, applyModificationsAcrossRuntimes, fuzz} = require('./fuzzer_multi_proc.js');

if (global.gc) {
            global.gc(); // run code with --expose-gc flag to trigger 
        } else {
            console.warn('Garbage collection is not exposed');
        }
// Function to process a chunk of tests
function processTestChunk({ testChunk, snippets, rounds, outputDir, chunkId }) {
    //for (let round = 1; round <= rounds; round++) {
        const roundDir = `${outputDir}/chunk_${chunkId}`;
        fuzz(testChunk, snippets, rounds, roundDir);
    //}

    
    // Notify parent process when done
    process.send("done");
}

// Listen for messages from the parent process
process.on('message', (data) => {
   // if (global.gc) {
    //    global.gc(); // run code with --expose-gc flag to trigger 
   // } else {
     //   console.warn('Garbage collection is not exposed');
   // }
    processTestChunk(data);
});
