(async function(){
    try {
        var addresses = await Deno.resolveDns("google.com", "A");
        addresses.forEach((address, index) => {
            console.log(`IP Address ${index + 1}: ${address}`);
        });
    } catch (err) {
      //  console.error('DNS resolution error:', err);
    }
})();