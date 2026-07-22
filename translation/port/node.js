var http = require('http');
var port = 8092;
(async function(){
  var server = http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Server is up!\n");
  });

  await new Promise((resolve) => {
    server.listen(port, () => {
      console.log(`Server running at http://localhost:${port}/`);
      resolve();
    });
  });

  async function makeRequest() {
    var url = `http://localhost:${port}/`;
    try {
      var response = await fetch(url);
      var data = await response.text();
      console.log('Response:', data);
    } catch (error) {
      console.error('Error:', error);
    }
  }
  await makeRequest();

  setTimeout(() => {
    server.close(() => {
      console.log("Server closed after 1.5 seconds.");
    });
  }, 1500);

})();