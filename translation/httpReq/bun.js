(async function() {
  var url = "https://example.com";

  try {
    var response = await fetch(url);
    var data = await response.text();
    console.log('Response:', data);
  } catch (error) {
    console.error('Error:', error);
  }
})();