import { writeFileSync, unlinkSync} from "node:fs";
(function () {
  writeFileSync("./BunOutput.txt", "file is written");

  //delete file
  unlinkSync("./BunOutput.txt");
})();
