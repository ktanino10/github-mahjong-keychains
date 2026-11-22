import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { build } from "esbuild";

const root = dirname(fileURLToPath(import.meta.url));
const project = dirname(root);
const output = join(project, "docs");
const fonts = join(root, "assets/fonts");
const assets = join(project, "print-package/source/assets");
await mkdir(output, { recursive: true });
const result = await build({
  entryPoints: [join(root, "app.ts")],
  bundle: true,
  minify: true,
  write: false,
  format: "iife",
  target: ["es2022"],
  legalComments: "inline",
});
const escapeHtml = (text) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
const [template, rawCss, model, poster, displayFont, monoFont, branch, octocat, chun, haku, iisou, ...licenses] = await Promise.all([
  readFile(join(root, "index.html"), "utf8"),
  readFile(join(root, "styles.css"), "utf8"),
  readFile(join(root, "assets/keychains.glb")),
  readFile(join(root, "poster.jpg")),
  readFile(join(fonts, "BigShoulders-Bold.ttf")),
  readFile(join(fonts, "DMMono-Regular.ttf")),
  readFile(join(assets, "git-branch-24.svg"), "utf8"),
  readFile(join(assets, "github-invertocat.svg"), "utf8"),
  readFile(join(assets, "chun-custom.svg"), "utf8"),
  readFile(join(assets, "haku-supplied-icon.svg"), "utf8"),
  readFile(join(assets, "iisou-ducky-silhouette.svg"), "utf8"),
  readFile(join(root, "node_modules/three/LICENSE"), "utf8"),
  readFile(join(fonts, "BigShoulders-OFL.txt"), "utf8"),
  readFile(join(fonts, "DMMono-OFL.txt"), "utf8"),
  readFile(join(assets, "octicons-LICENSE.txt"), "utf8"),
]);
const css = rawCss
  .replace("__DISPLAY_FONT__", displayFont.toString("base64"))
  .replace("__MONO_FONT__", monoFont.toString("base64"));
const js = result.outputFiles[0].text.replaceAll("</script", "<\\/script");
const replacements = {
  "/*__STYLES__*/": css,
  "/*__APP__*/": js,
  "__MODEL_DATA__": model.toString("base64"),
  "__POSTER__": poster.toString("base64"),
  "__BRANCH_ICON__": branch,
  "__OCTOCAT_ICON__": octocat,
  "__CHUN_ICON__": chun,
  "__HAKU_ICON__": haku,
  "__IISOU_ICON__": iisou,
  "__LICENSES__": escapeHtml(licenses.join("\n\n-------------------------------\n\n")),
};
let html = template;
for (const [key, value] of Object.entries(replacements)) {
  if (!html.includes(key)) throw new Error(`Missing build placeholder: ${key}`);
  html = html.replace(key, () => value);
}
if (/__(MODEL_DATA|POSTER|APP|STYLES|DISPLAY_FONT|MONO_FONT)__/.test(html)) {
  throw new Error("An unresolved HTML build placeholder remains.");
}
const filename = "index.html";
await writeFile(join(output, filename), html, "utf8");
await writeFile(join(project, "validation/html-manifest.json"), JSON.stringify({
  file: `docs/${filename}`,
  bytes: Buffer.byteLength(html),
  sha256: createHash("sha256").update(html).digest("hex"),
  modelSha256: createHash("sha256").update(model).digest("hex"),
  offline: true,
  externalAssets: false,
  languages: ["ja", "en"],
  runtime: "Three.js, GLTFLoader and OrbitControls, bundled with their MIT license",
}, null, 2));
console.log(`Created ${filename}: ${(Buffer.byteLength(html) / 1048576).toFixed(2)} MiB, entirely self-contained.`);
