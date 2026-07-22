var dns = require('dns');
(async function(){
  try {
    var addresses = await dns.promises.resolve4("google.com");
    addresses.forEach((address, index) => {
      console.log(`IP Address ${index + 1}: ${address}`);
    });
  } catch (err) {
    console.error('DNS resolution error:', err);
  }
})();