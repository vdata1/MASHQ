var { spawn } = require('child_process');
(async function(){
    var proc = await spawn("node", ["--version"]);
    console.log("subprocess forked");
    await proc.kill('SIGINT');
    console.log("subprocess killed");
})();
