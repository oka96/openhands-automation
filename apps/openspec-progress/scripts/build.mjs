import { build } from "esbuild";
import { copyFile, mkdir, readFile, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateApp } from "./validate.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

const result = await build({
  absWorkingDir: root,
  entryPoints: ["src/extension.js"],
  outfile: "dist/extension.js",
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2022",
  splitting: false,
  sourcemap: false,
  legalComments: "none",
  metafile: true,
  loader: { ".css": "text" },
  plugins: [{
    name: "embedded-raw-source",
    setup(builder) {
      builder.onResolve({ filter: /\?raw$/ }, ({ path: request, resolveDir }) => ({
        path: path.resolve(resolveDir, request.slice(0, -4)),
        namespace: "embedded-raw-source",
      }));
      builder.onLoad({ filter: /.*/, namespace: "embedded-raw-source" }, async ({ path: filename }) => {
        // Encode the Node collector as data: it is executed by the server, never
        // imported into the browser. UTF-8 decoding preserves its source exactly.
        const encoded = (await readFile(filename)).toString("base64");
        return {
          contents: `export default new TextDecoder().decode(Uint8Array.from(atob(${JSON.stringify(encoded)}), character => character.charCodeAt(0)));`,
          loader: "js",
          watchFiles: [filename],
        };
      });
    },
  }],
});

if (Object.keys(result.metafile.outputs).length !== 1) {
  throw new Error("The App must build to exactly one browser module.");
}
for (const output of Object.values(result.metafile.outputs)) {
  if (output.imports.length !== 0) throw new Error("The App bundle contains an unresolved import.");
  if (!output.exports.includes("activate")) throw new Error("The App bundle must export activate.");
}

await validateApp(root, { dist: true });
await copyFile(path.join(dist, "extension.js"), path.join(root, "extension.js"));
console.log("Built and validated extension.js (one self-contained browser module).");
