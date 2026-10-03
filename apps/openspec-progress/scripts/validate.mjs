import { execFile } from "node:child_process";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const run = promisify(execFile);
const defaultRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export async function validateApp(root = defaultRoot, { dist = false } = {}) {
  const manifest = JSON.parse(await readFile(path.join(root, "canvas-extension.json"), "utf8"));
  if (manifest.schema_version !== 1 || manifest.name !== "openspec-progress"
      || manifest.version !== "0.1.0" || manifest.entrypoint !== "extension.js"
      || manifest.display_name !== "OpenSpec progress") {
    throw new Error("Unexpected OpenSpec progress App manifest metadata.");
  }
  const pages = manifest.contributes?.pages;
  if (!Array.isArray(pages) || pages.length !== 1 || pages[0].id !== "progress"
      || pages[0].path !== "/progress" || pages[0].title !== "OpenSpec progress"
      || pages[0].nav_label !== "OpenSpec progress") {
    throw new Error("The manifest must declare only the OpenSpec progress page.");
  }
  if (dist) {
    const files = await readdir(path.join(root, "dist"), { recursive: true });
    if (files.length !== 1 || files[0] !== manifest.entrypoint) {
      throw new Error("Build output must contain exactly dist/extension.js.");
    }
  }
  const entrypoint = path.join(root, dist ? "dist" : "", manifest.entrypoint);
  const source = await readFile(entrypoint, "utf8");
  if (!source.trim()) throw new Error("The browser module is empty.");
  if (!/\bexport\s*(?:\{[^}]*\bactivate\b[^}]*\}|(?:async\s+)?function\s+activate\b)/m.test(source)) {
    throw new Error("The browser module must export activate.");
  }
  const forbidden = [
    [/(?:^|[;}\n])\s*import\s+(?:[^"'()]*?\s+from\s+)?["'][^"']+["']/m, "external import"],
    [/\bimport\s*\(/, "dynamic import"],
    [/\bexport\s+[^;]*?\sfrom\s*["']/m, "re-exported dependency"],
    [/\b(?:require\s*\(|module\.exports)/, "CommonJS dependency"],
    [/\b(?:process\s*\.|Buffer\s*\.|global\s*\.|__dirname\b|__filename\b)/, "Node-only global"],
    [/sourceMappingURL=/, "source-map reference"],
  ];
  for (const [pattern, description] of forbidden) {
    if (pattern.test(source)) throw new Error(`The browser module contains a ${description}.`);
  }
  await run(process.execPath, ["--check", entrypoint]);
  return true;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    await validateApp();
    await validateApp(defaultRoot, { dist: true });
    const [published, built] = await Promise.all([
      readFile(path.join(defaultRoot, "extension.js")),
      readFile(path.join(defaultRoot, "dist", "extension.js")),
    ]);
    if (!published.equals(built)) throw new Error("extension.js is stale; run npm run build.");
    console.log("OpenSpec progress App manifest and browser module are valid.");
  } catch (error) {
    console.error(`App validation failed: ${error.message}`);
    process.exitCode = 1;
  }
}
