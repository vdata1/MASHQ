(async function(){
    try {
        var addresses = await Bun.dns.lookup("google.com", { family: 4, ttl: true });
        addresses.forEach((address, index) => {
            console.log(`IP Address ${index + 1}: ${address.address}`);
        });
    } catch (err) {
        console.error('DNS resolution error:', err);
    }
})(); 