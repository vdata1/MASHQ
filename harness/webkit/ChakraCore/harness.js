if (typeof gc === "undefined") {
  globalThis.gc = () => {
    console.log("gc called (no-op)");
  };
}

/*if (typeof load === "undefined") {
  globalThis.load = (path) => {
    console.log(`Loading file: ${path}`);
  };
}*/

if (typeof load === "undefined") {
  globalThis.load = (filePath) => {
    try {
      const fullPath = path.resolve(filePath);
      const content = fs.readFileSync(fullPath, "utf-8");
      console.log(`File loaded: ${fullPath}`);
      console.log(content);
      return content;
    } catch (err) {
      console.error(`Error loading file: ${err.message}`);
    }
  };
}

if (typeof print === "undefined") {
  globalThis.print = console.log;
}

if (typeof quit === "undefined") {
  globalThis.quit = () => {
    console.log("Exiting script");
    process.exit(0);
  };
}

var WScript = {
  _jscGC: gc,
  _jscLoad: load,
  _jscPrint: print,
  _jscQuit: quit,
  _convertPathname: function (dosStylePath) {
    return dosStylePath.replace(/\\/g, "/");
  },
  Arguments: ["summary"],
  Echo: function () {
    WScript._jscPrint.apply(this, arguments);
  },
  LoadScriptFile: function (path) {
    WScript._jscLoad(WScript._convertPathname(path));
  },
  Quit: function () {
    WScript._jscQuit();
  },
};

function CollectGarbage() {
  WScript._jscGC();
}

function $ERROR(e) {}
