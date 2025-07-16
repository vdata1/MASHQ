var port = 8090;
(async function(){
  var server = Deno.serve({
  onListen() {
      console.log(`Server running at http://localhost:${ port }/`);
  },port: port }, req => { 
      return new Response('Server is up!\n', { headers: { 'Content-Type': 'text/plain' } });
});

//console.log(`Server running at http://localhost:${port}/`);

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

await makeRequest();

setTimeout(() => {
  server.shutdown();
  console.log("Server closed after 1.5 seconds.");
}, 1500);
})();