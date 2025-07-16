var http = require('http');
var port = 8092;
(async function(){
  var server = await http.createServer((req, res) => {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Server is up!\n");
  }).listen(port, () => {
    console.log(`Server running at http://localhost:${port}/`)});
  
    /*
  server.listen(port, () => {
    console.log(`Server running at http://localhost:${port}/`);
  
    var options = {
      hostname: "localhost",
      port: port,
      path: "/",
      method: "GET",
    };
  
    var req = http.request(options, (res) => {
      let data = "";
  
      res.on("data", (chunk) => {
        data += chunk;
      });
  
      res.on("end", () => {
        console.log("Response:", data);
      });
    });
  
    req.on("error", (e) => {
      console.error(`Problem with request: ${e.message}`);
    });
  
    req.end();
  });
  */
  async function makeRequest() {
    var url = `http://localhost:${ port }/`;
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
