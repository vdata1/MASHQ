const estraverse = require('estraverse');
const {createAST, readFileIfExists} = require("./fileUtils.js");

function injectFlagNode(ast, selectedNode, flagNode){
    //console.log(selectedNode);
    if (global.gc) {
        global.gc(); // run code with --expose-gc flag to trigger 
    } else {
        console.warn('Garbage collection is not exposed');
    }
    estraverse.replace(ast, {
        enter(node, parent) {
            // Collect nodes based on node type and modification type
            if (selectedNode == node) {
                    var randomIndex = 0; 
                    console.log("Node detected...");//, node);
                    //node.body = [...node.body, ...flagNode]; // Insert the flag node after the candidate node
                    if(Array.isArray(node.body)){
                        randomIndex = Math.floor(Math.random() * node.body.length);
                        //node.body.push(flagNode);
                        node.body.splice(randomIndex, 0, flagNode);
                        //console.log("parent.body: ", parent.body);
                    } else if(node.body && node.body.body && node.body.length > 0 && Array.isArray(parent.body.body)){
                        randomIndex = Math.floor(Math.random() * node.body.body.length);
                        //node.body.body.push(flagNode);
                        node.body.body.splice(randomIndex, 0, flagNode);
                        //console.log("parent.body.body: ", parent.body.body);
                    } /*else if(node.body && parent.body.body && node.body.length > 0 && Array.isArray(parent.body.body)){
                        parent.body.body.push(flagNode);
                        //console.log("parent.body.body: ", parent.body.body);
                    }*/
                    else{
                        console.log("inject_ast to biggining");
                        ast.body.unshift(flagNode);
                    }
                    //console.log(parent.body);
                    //console.log("parent body: ", node.body);
                    //parent.body = [...parent.body, ...flagNode]; // Insert the flag node after the candidate node
                    /*
                    const index = parent.body.indexOf(node);
                    if (index !== -1) {
                        parent.body.splice(index + 1, 0, flagNode); // Insert the flag node after the candidate node
                    }
                    console.log("parent body: ", parent.body);
                    */
            }
        }
    });
    return ast;
}
function markLocation(ast, modification, snippetAST, round, mergeAST){
    global.gc();
    //, addtionalSnippet=null) {
    //ast, modification, snippets, round, additionalTestAST
    //console.log("ast size: ", ast)
    //console.log("mergeAST marklocation: ", mergeAST);
    let candidateNodes = [];
    let flagNode; 
    //ast.body.push({type: 'BeginningOfFile'});
    //ast.body.push({type: 'EndOfFile'});
    // Traverse the AST to collect candidate nodes for modification
    estraverse.traverse(ast, {
        enter(node, parent) {
            // Collect nodes based on node type and modification type
            if (isValidNodeForModification(node, parent, modification) || node.type === 'BeginningOfFile' || node.type === 'EndOfFile') {
                console.log("Adding interesting transfer node...");
                candidateNodes.push({ node, parent });
            }
        }
    });
    
    
    // Select a random node from the candidates
    if (candidateNodes.length === 0) {
        //console.log("ast size: ", ast)
        console.log(`No valid nodes found for modification: ${modification}`);
        modification = "skip";
        flagNode = {
            type: 'Identifier',
            name: `//round: ${round}, modification: ${modification}`,
            leadingComments: [{
              type: 'Line',
              value: `round: ${round}, modification: ${modification}`
            }],
            _fuzzFlag: {
                "operation": modification,
                //"parentNode": selectedNode.parent ? selectedNode.parent.type : null,
                //"snippetAST": snippetAST, // Mark snippet for injection
                //"mergeAST": modification === 'append' || modification === 'transfer' ? mergeAST : null, // Mark AST for merging
                //"addtionalSnippet": modification === 'append' || modification === 'transfer' ? addtionalSnippet : null,
            }
          };
        ast.body.push(flagNode);  //injectFlagNode(ast, selectedNode.node, flagNode); //Program
        //console.log("markLocation AST:", ast);
        const nodeInfo = {
            node: flagNode._fuzzFlag,
            //parent: flagNode.parent,
            operation: modification
        };
    
        // Return the selected node's location and type of operation
        return {ast, nodeInfo}  
    }
    else{
        console.log("Available options: ", candidateNodes.length, " modification: ", modification);
        const randomPossition = Math.floor(Math.random() * candidateNodes.length+2); 
        if((modification === 'inject_snippet') && randomPossition > candidateNodes.length){
            if(randomPossition - candidateNodes.length == 1){
                modification = 'inject_beggining';
            }else{
                modification = 'inject_end';
            }
        }
        const randomIndex = Math.floor(Math.random() * candidateNodes.length);
        console.log("Selected option: ", randomIndex)
        const selectedNode = candidateNodes[randomIndex];
        //console.log("Selected Node: ", selectedNode);
        /*
        if(selectedNode.node.type == "BeginningOfFile"){
            modification = 'inject_beggining';
        }
        else if(selectedNode.node.type == "EndOfFile"){
            modification = 'inject_end';  
        }
        */
        // Add a flag (metadata) to the selected node indicating the operation
        flagNode = {
            type: 'Identifier',
            name: `//round: ${round}, modification: ${modification}`,
            leadingComments: [{
              type: 'Line',
              value: `round: ${round}, modification: ${modification}`
            }],
            _fuzzFlag: {
                "operation": modification,
                "parentNode": selectedNode.parent ? selectedNode.parent.type : ast,
                "snippetAST": snippetAST, // Mark snippet for injection
                "mergeAST": mergeAST, // Mark AST for merging
                //"addtionalSnippet": modification === 'append' || modification === 'transfer' ? addtionalSnippet : null,
            }
          };
        //flagNode.parent = selectedNode.parent; 
        //inject flagNode to AST after the selected node. 
        ast = injectFlagNode(ast, selectedNode.node, flagNode);
        //console.log("markLocation AST:", ast);
        const nodeInfo = {
            node: flagNode._fuzzFlag,
            //parent: flagNode.parent,
            operation: modification
        };
    
        // Return the selected node's location and type of operation
        return {ast, nodeInfo}
    }
    
}

function hasBody(node) {
    return node && node.body !== undefined && node.body !== null;
} 

function isValidNodeForModification(node, parent, modification) {
    const nodeType = getNodePath(node); 
    //console.log(`NodeType: ${nodeType}`);
    if (modification === 'delete') {
        return (nodeType != 'Program' && nodeType != 'FunctionDeclaration'  && (nodeType == 'ArrowFunctionExpression' || nodeType == 'BlockStatement' || nodeType == 'ExpressionStatement'))// && !node._fuzzFlag;
    }
    if (modification === 'inject_snippet') {
        return hasBody(node) && ((nodeType == 'BlockStatement' && ( parent.type == 'Program' || parent.type == 'FunctionDeclaration' || parent.type == 'ExpressionStatement' || parent.type == 'ArrowFunctionExpression')) || nodeType == 'Program' || nodeType == 'BlockStatement')// && !node._fuzzFlag;
    }
    if (modification === 'transfer') {
        return hasBody(node) && (nodeType == 'BlockStatement' || nodeType == 'Program' || nodeType == 'FunctionDeclaration' || nodeType == "ExpressionStatement" || nodeType == "ArrowFunctionExpression"); //&& ((nodeType == 'BlockStatement' && ( parent.type == 'Program' || parent.type == 'FunctionDeclaration' || parent.type == 'ExpressionStatement' || parent.type == 'ArrowFunctionExpression'))  || nodeType == 'BlockStatement' || nodeType == 'Program')// && !node._fuzzFlag;
    }
    if (modification === 'append') {
        return (nodeType == 'Program')//&& !node._fuzzFlag; //'BlockStatement' || node.type !== 'FunctionDeclaration';
    }
    return false;
}

function getNodePath(node) {
    return [node.type];
}

module.exports = {
    markLocation
};
