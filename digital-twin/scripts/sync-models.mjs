// Copies the printable 3MF parts from ../3d-files/3mf into public/models so the
// web app always renders the exact files that live in the project.
import { cpSync, mkdirSync, readdirSync, rmSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const src = join(root, "..", "3d-files", "3mf");
const dst = join(root, "public", "models");

// URL-safe file names (e.g. "Tube_Curved_90°" -> "Tube_Curved_90deg")
const safe = (name) => name.replace(/°/g, "deg").replace(/[^\w.\-]/g, "_");

rmSync(dst, { recursive: true, force: true });
let count = 0;
const walk = (dir, rel = "") => {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, join(rel, safe(entry)));
    else if (entry.toLowerCase().endsWith(".3mf")) {
      mkdirSync(join(dst, rel), { recursive: true });
      cpSync(full, join(dst, rel, safe(entry)));
      count++;
    }
  }
};
walk(src);
console.log(`[sync-models] ${count} 3MF files -> public/models`);
