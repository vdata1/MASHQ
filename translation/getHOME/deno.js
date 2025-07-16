var homeDir = Deno.env.get('HOME') || Deno.env.get('USERPROFILE'); // for Windows compatibility
Deno.chdir(homeDir);  
console.log('Current HOME Directory:', Deno.cwd());
