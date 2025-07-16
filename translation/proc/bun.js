(async function(){
    var proc = await Bun.spawn(["bun", "--version"]);
    console.log("subprocess forked")
    await proc.exited;
    console.log("subprocess killed"); 
})();