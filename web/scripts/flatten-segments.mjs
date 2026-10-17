// Next 16's static export writes each route's segment prefetch file as nested folders
// (review/claim/__next.review/claim/__PAGE__.txt), but the client router requests a flat
// name (review/claim/__next.review.claim.__PAGE__.txt). Static hosts such as Firebase
// Hosting serve files exactly as uploaded, so those requests 404 and a client-side
// navigation can end on the "page could not be found" screen. Copy each file to the
// flat name as well.
import { copyFileSync, readdirSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "out");
let copied = 0;

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const path = join(dir, entry.name);
    if (entry.name.startsWith("__next.")) flatten(dir, path);
    else walk(path);
  }
}

// <dir>/__next.a/b/__PAGE__.txt -> <dir>/__next.a.b.__PAGE__.txt
function flatten(dir, segmentDir) {
  for (const entry of readdirSync(segmentDir, { withFileTypes: true, recursive: true })) {
    if (!entry.isFile()) continue;
    const file = join(entry.parentPath, entry.name);
    copyFileSync(file, join(dir, relative(dir, file).split(/[\\/]/).join(".")));
    copied++;
  }
}

walk(out);
console.log(`flatten-segments: copied ${copied} segment file(s) to the flat names the router requests`);
