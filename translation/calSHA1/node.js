var crypto = require('crypto');
(async function(){
    var inputString = 'test';
    var hash = await crypto.createHash('sha1');
    await hash.update(inputString);
    console.log(hash.digest('hex'));
})(); 