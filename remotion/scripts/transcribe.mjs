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
import { existsSync, mkdirSync, writeFileSync, createReadStream } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

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
console.log(`→ Extracting audio from ${videoArg} with FFmpeg…`);
try {
  execFileSync(
    "ffmpeg",
    ["-y", "-i", videoPath, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", audioPath],
    { stdio: ["ignore", "ignore", "inherit"] }
  );
} catch {
  fail("FFmpeg failed. Is it installed and on your PATH? (ffmpeg -version)");
}
console.log(`  audio → public/audio.mp3`);

// --- Whisper: transcribe with word-level timestamps ------------------------
console.log("→ Transcribing with OpenAI Whisper (word timestamps)…");
const openai = new OpenAI();
let result;
try {
  result = await openai.audio.transcriptions.create({
    file: createReadStream(audioPath),
    model: "whisper-1",
    response_format: "verbose_json",
    timestamp_granularities: ["word"],
  });
} catch (err) {
  fail(`Whisper request failed: ${err?.message ?? err}`);
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
console.log(`\nNext: run "npm run find -- \\"your phrase\\"" to get timestamps,`);
console.log(`then add graphics in src/data/graphics.ts and "npm run studio".`);
