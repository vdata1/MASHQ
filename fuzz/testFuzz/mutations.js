const estraverse = require('estraverse');

// Perform the fuzzing operation for a given round
function performRound(testAST, snippets, round, runtime) {
    // Choose a random mutation based on weighted probability
    const mutationType = chooseMutation();

    switch (mutationType) {
        case 'deleteSubtree':
            deleteSubtree(testAST);
            break;
        case 'injectSnippet':
            injectSnippet(testAST, snippets[runtime]);
            break;
        case 'combineAndInject':
            combineAndInject(testAST, snippets[runtime]);
            break;
        case 'appendASTs':
            appendASTs(testAST, snippets[runtime]);
            break;
    }

    return testAST;
}

// Function to choose mutation based on probability
function chooseMutation() {
    const random = Math.random();
    if (random < 0.2) return 'deleteSubtree';
    if (random < 0.5) return 'injectSnippet';
    if (random < 0.8) return 'combineAndInject';
    return 'appendASTs';
}

// Mutation: delete a random subtree from the AST
function deleteSubtree(ast) {
    estraverse.replace(ast, {
        enter: (node, parent) => {
            if (Math.random() < 0.2) return estraverse.VisitorOption.Remove;
        }
    });
}

// Mutation: inject a code snippet at a random location in the AST
function injectSnippet(ast, snippets) {
    const snippet = selectRandomSnippet(snippets);
    const snippetAST = createAST(snippet.content);

    estraverse.traverse(ast, {
        enter: (node, parent) => {
            if (Math.random() < 0.1) {
                parent.body.splice(Math.floor(Math.random() * parent.body.length), 0, snippetAST.body[0]);
                return estraverse.VisitorOption.Break;
            }
        }
    });
}

// Mutation: combine two ASTs, injecting one snippet
function combineAndInject(ast, snippets) {
    const snippet = selectRandomSnippet(snippets);
    const snippetAST = createAST(snippet.content);

    // Find two positions to combine
    estraverse.traverse(ast, {
        enter: (node, parent) => {
            if (Math.random() < 0.1) {
                parent.body = [snippetAST.body[0], ...parent.body];
                return estraverse.VisitorOption.Break;
            }
        }
    });
}

// Mutation: append two ASTs
function appendASTs(ast, snippets) {
    const snippet = selectRandomSnippet(snippets);
    const snippetAST = createAST(snippet.content);

    estraverse.traverse(ast, {
        enter: (node, parent) => {
            if (Math.random() < 0.1) {
                parent.body.push(snippetAST.body[0]);
                return estraverse.VisitorOption.Break;
            }
        }
    });
}

// Helper: Select a random snippet
function selectRandomSnippet(snippets) {
    return snippets[Math.floor(Math.random() * snippets.length)];
}

module.exports = {
    performRound
};