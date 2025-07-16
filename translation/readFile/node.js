var fs = require('fs');
(async function(){
fs.readFile('/etc/passwd', 'utf8', (err, data) => {
  console.log(data);
});
})();