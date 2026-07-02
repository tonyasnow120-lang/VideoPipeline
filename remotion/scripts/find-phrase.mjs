#!/usr/bin/env node
/**
 * Helper for Step 2 (mapping graphics to speech): find where a phrase is
 * spoken so you know the start timestamp to give a graphic.
 *
 * Usage:
 *   node scripts/find-phrase.mjs "the process"
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const transcriptPath = resolve(__dirname, "../src/data/transcript.json");

if (!existsSync(transcriptPath)) {
  console.error("No transcript yet. Run: npm run transcribe -- public/source.mp4");
  process.exit(1);
}

const phrase = (process.argv.slice(2).join(" ") || "").trim().toLowerCase();
if (!phrase) {
  console.error('Usage: npm run find -- "phrase to locate"');
  process.exit(1);
}

const { words } = JSON.parse(readFileSync(transcriptPath, "utf8"));
const needle = phrase.split(/\s+/);
const clean = (s) => s.toLowerCase().replace(/[^a-z0-9']/g, "");

const hits = [];
for (let i = 0; i + needle.length <= words.length; i++) {
  let match = true;
  for (let j = 0; j < needle.length; j++) {
    if (clean(words[i + j].word) !== clean(needle[j])) {
      match = false;
      break;
    }
  }
  if (match) {
    hits.push({ start: words[i].start, end: words[i + needle.length - 1].end });
  }
}

if (hits.length === 0) {
  console.log(`No match for "${phrase}".`);
  process.exit(0);
}

console.log(`Found "${phrase}" ${hits.length} time(s):`);
for (const h of hits) {
  console.log(`  start ${h.start.toFixed(2)}s  →  end ${h.end.toFixed(2)}s`);
}
