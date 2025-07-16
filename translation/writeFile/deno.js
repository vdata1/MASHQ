(async function(){
    var encoder = new TextEncoder();
    var data = encoder.encode("file written\n");
    await Deno.writeFile("./DenoOutput.txt", data); 
    
    //delete the written file
    await Deno.remove("./DenoOutput.txt");        
})();