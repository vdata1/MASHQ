(async function(){
    var addresses = await Bun.dns.resolve("google.com", {ttl:true});
    addresses.forEach((address, index) => {
        console.log(`IP Address ${index + 1}: ${address.address}`);
    });
})();
