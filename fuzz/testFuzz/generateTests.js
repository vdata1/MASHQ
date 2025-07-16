function performRoundWithFlags(ast, runtime){//snippetAST, modification, locations) {
    const clonedAST = cloneAST(ast);  // Clone the AST before applying changes
    return applyModifications(clonedAST, runtime);  // Apply changes on the clone
}
