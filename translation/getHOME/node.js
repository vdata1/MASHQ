var process = require('process');
var homeDir = process.env.HOME || process.env.USERPROFILE; // for Windows compatibility
process.chdir(homeDir);
console.log('Current HOME Directory:', process.cwd());