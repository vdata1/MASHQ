const fs = require('node:fs');
const path = require('node:path');
const esprima = require('esprima');
const workingFilesList = require('../no_error_files/all.json');

if (global.gc) {
    global.gc(); // run code with --expose-gc flag to trigger 
} else {
    console.warn('Garbage collection is not exposed');
}



// Helper function to collect all files recursively in a directory
if (global.gc) {
            global.gc(); // run code with --expose-gc flag to trigger 
        } else {
            console.warn('Garbage collection is not exposed');
        }
function collectFilesRecursively(dir) {
    let results = [];
    const list = fs.readdirSync(dir);

    list.forEach(file => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat && stat.isDirectory()) {
            results = results.concat(collectFilesRecursively(fullPath));
        } else{
            if( workingFilesList["test"].indexOf(fullPath) >-1 || workingFilesList["v8"].indexOf(fullPath) >-1 || workingFilesList["test262"].indexOf(fullPath) >-1 || workingFilesList["webkit"].indexOf(fullPath) >-1 ){
                results.push(fullPath);
            }
        }
    });

    return results;
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

// Read test files recursively and return their content and names
function readTestFiles(dirs, numTests = 'all') {
    let testFiles_unshuffle = []; 
    for(let i=0; i<dirs.length; i++){
        testFiles_unshuffle = testFiles_unshuffle.concat(shuffleArray(collectFilesRecursively(dirs[i])));//.slice(1800,2000);
    }
    let testFiles = shuffleArray(testFiles_unshuffle);
    if (numTests !== 'all') {
        testFiles = testFiles.slice(0, parseInt(numTests));
    }

    //. console.log(testFiles_unshuffle);
    console.log(testFiles.length, " test files found");
    //console.log("Test files: ", testFiles);


    // Read the content of each test file
    const tests = testFiles.map(file => ({
        name: file,
        content: fs.readFileSync(file, 'utf-8')
    }));

    console.log(tests.length, " test files read");
    return tests;
}

// Read snippet files recursively and handle directory structure for each runtime
function readSnippetFiles(snippetsDir) {
    const snippetDirs = fs.readdirSync(snippetsDir);
    const snippets = {};

    snippetDirs.forEach(snippetDir => {
        const fullSnippetPath = path.join(snippetsDir, snippetDir);
        // Check if it's a directory (expecting subdirectories for each snippet example)
        if (fs.statSync(fullSnippetPath).isDirectory()) {
            snippets[snippetDir] = {
                node: path.join(fullSnippetPath, 'node.js'), //readFileIfExists(path.join(fullSnippetPath, 'node.js')),
                deno: path.join(fullSnippetPath, 'deno.js'), //readFileIfExists(path.join(fullSnippetPath, 'deno.js')),
                bun: path.join(fullSnippetPath, 'bun.js'), //readFileIfExists(path.join(fullSnippetPath, 'bun.js'))
            };
        }
    });
    console.log(Object.keys(snippets).length, " snippet directories found");
    return snippets;
}

// Helper function to read a file if it exists and ensure it's not a directory
function readFileIfExists(filepath) {
    if (fs.existsSync(filepath) && fs.statSync(filepath).isFile()) {
        return fs.readFileSync(filepath, 'utf-8');
    } else {
        throw new Error(`Expected file not found: ${filepath}`);
    }
}


// Parse to AST 
function createAST(file){
    let ast = {};
    try{
        ast = esprima.parseScript(file, { loc: true, ecmaVersion: 2020 });
    }catch(err){
      console.log("Error while parsing Script, trying parseModule...")
      try{
       // console.log(file);
        console.log("trying parseModule")
        ast = esprima.parseModule(file, { sourceType: 'module' });
      }catch(err){
          console.log("Error while parsing Module: ", err ); 
          return ; 
      }
    }
    return ast; 
  }

module.exports = {
    readTestFiles,
    readSnippetFiles,
    createAST,
    readFileIfExists, 
};
