var dns = require('dns');
(async function(){
  await dns.resolve4("google.com", (err, addresses) => {
    if (err) {
     // console.error('DNS resolution error:', err);
      return;
    }
    addresses.forEach((address, index) => {
      console.log(`IP Address ${index + 1}: ${address}`);
    });
  });
  
})(); 
