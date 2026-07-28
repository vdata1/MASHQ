(function () {
  try {
    var encoder = new TextEncoder();
    var data = encoder.encode("file written\n");
    Deno.writeFileSync("./DenoOutput.txt", data);

    //delete the written file
    Deno.removeSync("./DenoOutput.txt");
  } catch (err) {
    console.error('Error:', err);
  }
})();