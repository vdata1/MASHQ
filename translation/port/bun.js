var port = 8091;

(async function(){
  var server = await Bun.serve({
    port: port,
    fetch(req) {
      return new Response("Server is up!\n", {
        headers: { "Content-Type": "text/plain" },
      });
    }, 
  }); 
  console.log(`Server running at http://localhost:${port}/`);
  
  async function makeRequest() {
    var url = `http://localhost:${port}/`;
    try {
      var response = await fetch(url);
      var data = await response.text();
      console.log("Response:", data);
    } catch (error) {
      console.error("Error:", error);
    }
  }
  
  makeRequest();
  
  setTimeout(() => {
    server.stop();
    console.log("Server closed after 1.5 seconds.");
  }, 1500);
  
})();