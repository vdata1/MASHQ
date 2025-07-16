import * as crypto from "https://deno.land/std@0.119.0/hash/mod.ts";
(async function(){
  var inputString = "test";
  var encoder = new TextEncoder();
  var data = encoder.encode(inputString);
  var hash = await crypto.createHash("sha1");
  hash.update(data);
  //crypto.toHex(hash.digest());
  var digestBytes = hash.digest();
  let hashHex = "";
  for (var byte of digestBytes) {
    hashHex += byte.toString(16).padStart(2, "0");
  }
  console.log(hashHex);
})();