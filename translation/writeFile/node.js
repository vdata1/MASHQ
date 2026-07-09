const fs = require("fs");
(async function () {
  try {
    await fs.writeFile("./NodeOutput.txt", "file written");
    await fs.unlink("./NodeOutput.txt");
  } catch (err) {}
})();
