var https = require('https');
(async function(){
  var options = {
    hostname: 'example.com',
    port: 443,
    path: '/',
    method: 'GET'
  };

  try {
    var data = await new Promise(function(resolve, reject) {
      var req = https.request(options, function(res) {
        var chunks = '';

        res.on('data', function(chunk) {
          chunks += chunk;
        });

        res.on('end', function() {
          resolve(chunks);
        });
      });

      req.on('error', function(e) {
        reject(e);
      });

      req.end();
    });

    console.log('Response:', data);
  } catch (error) {
    console.error('Error:', error);
  }
})();