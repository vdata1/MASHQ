(async function () {
  var fs = require("fs");
  try {
    await fs.writeFile("./NodeOutput.txt", "file written");
    await fs.unlink("./NodeOutput.txt");
  } catch (err) {}
})();
