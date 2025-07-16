(async function(){
    var output = await Bun.$`pwd`.text();
    console.log(output);    
})();