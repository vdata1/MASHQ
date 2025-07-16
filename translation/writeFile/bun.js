import { promises as fs } from "fs";

(async function () {
  await Bun.write("./BunOutput.txt", "file is written");
  await fs.unlink("./BunOutput.txt");
})();
