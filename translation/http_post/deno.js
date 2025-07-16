(async function () {
  var url = "https://example.com";

  try {
    var response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ key: "value" }),
    });

    var data = await response.text();
    console.log("Response:", data);
  } catch (error) {
    console.error("Error:", error);
  }
})();
