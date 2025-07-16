(async function () {
  var command = new Deno.Command("deno", {
    args: ["--version"],
    stdout: "piped",
    stderr: "piped",
  });

  var child = command.spawn();
  console.log("subprocess forked");

  await child.kill("SIGTERM");
  console.log("subprocess killed");
})();
