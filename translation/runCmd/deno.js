(async function(){
    let cmd = new Deno.Command("pwd");
    let { code, stdout, stderr } = await cmd.output();
    console.log(new TextDecoder().decode(stdout));         
})();