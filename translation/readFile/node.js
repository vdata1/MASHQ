var fs = require('fs');
(async function(){
  try {
    var data = await fs.promises.readFile('/etc/passwd', 'utf8');
    console.log(data);
  } catch (err) {
    console.error('Error:', err);
  }
})();