(function () {
  var fs = require("node:fs");
  try {
    fs.writeFileSync("./NodeOutput.txt", "file written");
    fs.unlinkSync("./NodeOutput.txt");
  } catch (err) {}
})();
