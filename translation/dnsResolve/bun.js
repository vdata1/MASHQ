
import {dns} from "bun";
(async function(){
    var addresses = await dns.resolve("google.com", {ttl:true});
    addresses.forEach((address, index) => {
        console.log(`IP Address ${index + 1}: ${address.address}`);
    });
})();
