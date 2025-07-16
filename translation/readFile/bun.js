(async function(){
    var file = Bun.file("/etc/passwd");
    console.log(await file.text());
})();