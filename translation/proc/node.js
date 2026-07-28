var { spawn } = require('child_process');
(async function(){
    var proc = spawn("node", ["--version"]);
    console.log("subprocess forked");
    proc.kill('SIGTERM');
    await new Promise(function(resolve) {
      proc.on('exit', resolve);
    });
    console.log("subprocess killed");
})();