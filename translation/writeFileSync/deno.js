(function () {
  var encoder = new TextEncoder();
  var data = encoder.encode("file written\n");
  Deno.writeFileSync("./DenoOutput.txt", data);

  //delete the written file
  Deno.removeSync("./DenoOutput.txt");
})();
