var https = require("https");

(async function () {
  var options = {
    hostname: "example.com",
    port: 443,
    path: "/",
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  };

  // Create the request
  var req = https.request(options, (res) => {
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

  var bodyData = JSON.stringify({
    key: "value",
  });

  req.write(bodyData);

  req.end();
})();
