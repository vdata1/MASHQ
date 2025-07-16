(async function(){
    var text = await Deno.readTextFile("/etc/passwd");
    console.log(text);    
})();