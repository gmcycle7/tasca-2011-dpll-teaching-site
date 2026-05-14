// Copy the Python simulator's PNG outputs into web/public/figures/ so
// Vite can serve them at /figures/*.png. Run automatically before
// `npm run dev` and `npm run build`; can also be run manually after a
// fresh Python re-run via `npm run copy:figures`.

import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(__dirname, "..");
const projectRoot = resolve(webRoot, "..");
const srcDir = join(projectRoot, "results", "figures");
const dstDir = join(webRoot, "public", "figures");

mkdirSync(dstDir, { recursive: true });

if (!existsSync(srcDir)) {
  console.warn(
    `[copy:figures] source ${srcDir} does not exist; run the Python ` +
      "scripts under scripts/ first. Continuing with empty figures dir.",
  );
  process.exit(0);
}

let copied = 0;
for (const name of readdirSync(srcDir)) {
  if (!name.toLowerCase().endsWith(".png")) continue;
  const src = join(srcDir, name);
  const dst = join(dstDir, name);
  if (!statSync(src).isFile()) continue;
  copyFileSync(src, dst);
  copied += 1;
}
console.log(`[copy:figures] copied ${copied} PNG(s) from ${srcDir} → ${dstDir}`);
