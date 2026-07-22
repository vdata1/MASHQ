import process from "process";
var originalDir = process.cwd();
process.chdir(process.env.HOME || process.env.USERPROFILE);
console.log("Current HOME Directory:", process.cwd());
process.chdir(originalDir);