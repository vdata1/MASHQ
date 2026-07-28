(async function () {
  var command = new Deno.Command("deno", {
    args: ["--version"],
    stdout: "piped",
    stderr: "piped",
  });

  var child = command.spawn();
  console.log("subprocess forked");
  try {
    child.kill("SIGTERM");
  } catch (e) {
    // process may have already exited naturally before kill() ran; ignore
  }
  await child.status;
  console.log("subprocess killed");
})();