(async function(){
    var proc = Bun.spawn(["bun", "--version"]);
    console.log("subprocess forked");
    proc.kill();
    await proc.exited;
    console.log("subprocess killed");
})();