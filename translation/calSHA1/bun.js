(async function(){
    var hasher = new Bun.CryptoHasher("sha1");
    console.log(await hasher.update("test").digest('hex'));
})();


//const hasher = new Bun.CryptoHasher("sha1");
//hasher.update();