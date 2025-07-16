(async function(){
  var { exec } = require('child_process');
  exec('pwd', (err, stdout, stderr) => {
    console.log(stdout);
  });    
})();