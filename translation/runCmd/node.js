var { exec } = require('child_process');
(async function(){
  try {
    var stdout = await new Promise(function(resolve, reject) {
      exec('pwd', function(err, stdout, stderr) {
        if (err) {
          reject(err);
          return;
        }
        resolve(stdout);
      });
    });
    console.log(stdout);
  } catch (err) {
    console.error('Error:', err);
  }
})();