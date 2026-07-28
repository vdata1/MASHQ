import { writeFileSync, unlinkSync } from "node:fs";
(function () {
  try {
    writeFileSync("./BunOutput.txt", "file is written");

    //delete file
    unlinkSync("./BunOutput.txt");
  } catch (err) {
    console.error('Error:', err);
  }
})();