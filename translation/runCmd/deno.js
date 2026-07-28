(async function(){
    var cmd = new Deno.Command("pwd");
    var { code, stdout, stderr } = await cmd.output();
    console.log(new TextDecoder().decode(stdout));
})();