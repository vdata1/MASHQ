import process from "process"
process.chdir(process.env.HOME || process.env.USERPROFILE);
console.log("Current HOME Directory:", process.cwd());
