var fs = require("fs/promises");
(async function () {
  try {
    await fs.writeFile("./NodeOutput.txt", "file written");
    await fs.unlink("./NodeOutput.txt");
  } catch (err) {
    console.error('Error:', err);
  }
})();