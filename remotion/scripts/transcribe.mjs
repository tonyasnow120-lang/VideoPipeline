#!/usr/bin/env node
/**
 * Step 1 of the pipeline: extract audio with FFmpeg, transcribe with the
 * OpenAI Whisper API, and write a word-level timestamped transcript.
 *
 * Usage:
 *   OPENAI_API_KEY=sk-... node scripts/transcribe.mjs public/source.mp4
 *
 * Output:
 *   src/data/transcript.json   (words with { word, start, end } in seconds)
 *
 * The word timings are what let you place a graphic exactly when you start
 * saying the thing it illustrates.
 */
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, createReadStream } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

// Load remotion/.env if present (no dotenv dependency; works on any Node 18+).
try {
  const envFile = readFileSync(resolve(root, ".env"), "utf8");
  for (const line of envFile.split("\n")) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (m && !(m[1] in process.env)) {
      process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
} catch {
  // no .env — fine, the key may be exported in the shell
}

const videoArg = process.argv[2] ?? "public/source.mp4";
const videoPath = resolve(root, videoArg);
const audioPath = resolve(root, "public/audio.mp3");
const outPath = resolve(root, "src/data/transcript.json");

function fail(msg) {
  console.error(`\n✖ ${msg}\n`);
  process.exit(1);
}

if (!process.env.OPENAI_API_KEY) {
  fail("OPENAI_API_KEY is not set. Add it to remotion/.env or export it.");
}
if (!existsSync(videoPath)) {
  fail(`Source video not found: ${videoPath}\nPut your video in remotion/public/ or pass a path.`);
}

// --- FFmpeg: extract a mono 16kHz mp3 (small + Whisper-friendly) ------------
// Prefer the bundled binary from ffmpeg-static (installed by npm install);
// fall back to a system-wide ffmpeg on PATH.
let ffmpegBin = "ffmpeg";
try {
  const staticPath = createRequire(import.meta.url)("ffmpeg-static");
  if (staticPath && existsSync(staticPath)) ffmpegBin = staticPath;
} catch {
  // ffmpeg-static not installed (optional dependency) — use system ffmpeg
}

console.log(`→ Extracting audio from ${videoArg} with FFmpeg…`);
try {
  execFileSync(
    ffmpegBin,
    ["-y", "-i", videoPath, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", audioPath],
    { stdio: ["ignore", "ignore", "inherit"] }
  );
} catch (err) {
  if (err?.code === "ENOENT") {
    fail(
      "FFmpeg is not installed.\n" +
        "  Easiest fix: run \"npm install\" in the remotion folder (downloads a bundled FFmpeg), then retry.\n" +
        "  Or install it system-wide: winget install ffmpeg (Windows) / brew install ffmpeg (Mac),\n" +
        "  then CLOSE and REOPEN the launcher window so it sees the new PATH."
    );
  }
  fail(
    "FFmpeg ran but could not extract audio — the video file may be corrupt or in an unsupported format.\n" +
      "  See FFmpeg's output above for details."
  );
}
console.log(`  audio → public/audio.mp3`);

// --- Preflight: can we reach the OpenAI API at all? -------------------------
// "Connection error." from the SDK hides the real cause, so check first and
// report something actionable.
function describeError(err) {
  const parts = [];
  let e = err;
  while (e && parts.length < 5) {
    parts.push([e.code, e.message || String(e)].filter(Boolean).join(" — "));
    e = e.cause;
  }
  return parts.join("\n      caused by: ");
}

console.log("→ Checking connection to api.openai.com…");
try {
  const resp = await fetch("https://api.openai.com/v1/models", {
    headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
    signal: AbortSignal.timeout(20000),
  });
  if (resp.status === 401) {
    fail(
      "Your OpenAI API key was rejected (401).\n" +
        "  Open remotion/.env and check the key: it should start with sk-,\n" +
        "  with no quotes, spaces, or line breaks. Create a new key at\n" +
        "  https://platform.openai.com/api-keys if needed."
    );
  }
  if (resp.status === 403) {
    console.log(
      "  ⚠ the API answered 403 — OpenAI may not be available in your country/region,\n" +
        "    or a proxy is interfering. If the next step fails, that's why."
    );
  }
  if (resp.status === 429) {
    console.log(
      "  ⚠ your account is rate-limited or out of credit (429) — if the next step\n" +
        "    fails, add credit at https://platform.openai.com/settings/organization/billing"
    );
  }
  console.log("  connection OK");
} catch (err) {
  fail(
    "Cannot reach api.openai.com — this is a network problem on this computer,\n" +
      "  not an API key problem.\n" +
      `  Details: ${describeError(err)}\n` +
      "  Common fixes, in order of likelihood:\n" +
      "   1. Antivirus \"web protection\" blocking Node.js — allow node.exe, or turn\n" +
      "      off HTTPS/SSL scanning, then retry\n" +
      "   2. Using a VPN? Toggle it (OpenAI also requires a supported country)\n" +
      "   3. Firewall blocking outbound connections from Node.js\n" +
      "   4. Sanity check: open https://api.openai.com/v1/models in your browser —\n" +
      "      a JSON error page is GOOD (the API is reachable); no page at all means\n" +
      "      your network is blocking it"
  );
}

// --- Whisper: transcribe with word-level timestamps ------------------------
console.log("→ Transcribing with OpenAI Whisper (word timestamps)…");
const openai = new OpenAI({ maxRetries: 4, timeout: 10 * 60 * 1000 });
let result;
try {
  result = await openai.audio.transcriptions.create({
    file: createReadStream(audioPath),
    model: "whisper-1",
    response_format: "verbose_json",
    timestamp_granularities: ["word"],
  });
} catch (err) {
  fail(`Whisper request failed: ${describeError(err)}`);
}

const words = (result.words ?? []).map((w) => ({
  word: w.word,
  start: w.start,
  end: w.end,
}));

if (words.length === 0) {
  fail("No words returned. Check that the audio actually contains speech.");
}

mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(
  outPath,
  JSON.stringify({ text: result.text, duration: result.duration, words }, null, 2)
);

console.log(`\n✓ ${words.length} words → src/data/transcript.json`);
console.log(`  Full text length: ${result.text.length} chars`);
console.log(`\nNext: find your moments (step 3 in the GUI, or "npm run find -- \\"your phrase\\""),`);
console.log(`then add graphics (step 4 in the GUI, or edit src/data/graphics.json).`);
