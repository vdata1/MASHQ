const { exec } = require('child_process');
(async function(){
  exec('pwd', (err, stdout, stderr) => {
    console.log(stdout);
  });    
})();