#!/usr/bin/env node
/**
 * Local GUI for the pipeline: upload a video, transcribe, build graphics /
 * music / ad breaks with forms, launch Remotion Studio, render, download.
 *
 * Usage: npm run gui   →   http://localhost:4000
 *
 * Everything runs on your machine; the server binds to localhost only.
 * It writes the same JSON files (src/data/*.json) that Remotion Studio
 * imports, so saving in the GUI hot-reloads an open Studio tab.
 */
import express from "express";
import multer from "multer";
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const publicDir = join(root, "public");
const dataDir = join(root, "src", "data");
const outFile = join(root, "out", "video.mp4");
const PORT = 4000;

// Load remotion/.env into this process so spawned jobs inherit the API key.
try {
  for (const line of readFileSync(join(root, ".env"), "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (m && !(m[1] in process.env)) {
      process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
} catch {
  // no .env yet — the GUI will show a warning
}

// Resolve the Remotion CLI entry point (cross-platform, no npx needed).
const require = createRequire(import.meta.url);
const cliPkgPath = require.resolve("@remotion/cli/package.json", { paths: [root] });
const cliPkg = JSON.parse(readFileSync(cliPkgPath, "utf8"));
const remotionBin = join(
  dirname(cliPkgPath),
  typeof cliPkg.bin === "string" ? cliPkg.bin : cliPkg.bin.remotion
);

const app = express();
app.use(express.json({ limit: "5mb" }));

// --- Uploads ----------------------------------------------------------------
mkdirSync(publicDir, { recursive: true });

const videoUpload = multer({
  storage: multer.diskStorage({
    destination: publicDir,
    // The composition always reads public/source.mp4.
    filename: (_req, _file, cb) => cb(null, "source.mp4"),
  }),
  limits: { fileSize: 4 * 1024 * 1024 * 1024 },
});

const assetUpload = multer({
  storage: multer.diskStorage({
    destination: publicDir,
    filename: (_req, file, cb) =>
      cb(null, basename(file.originalname).replace(/[^\w.\- ]/g, "_")),
  }),
  limits: { fileSize: 1024 * 1024 * 1024 },
});

// --- Background jobs (transcribe / render) -----------------------------------
const jobs = {}; // name → { status: "running"|"done"|"error", log: [] }

function startJob(name, args) {
  if (jobs[name]?.status === "running") return false;
  const job = (jobs[name] = { status: "running", log: [] });
  const child = spawn(process.execPath, args, { cwd: root, env: process.env });
  const push = (buf) => {
    for (const raw of buf.toString().split(/\r?\n/)) {
      const line = raw.replace(/\x1b\[[0-9;]*[A-Za-z]/g, "").trimEnd();
      if (line) job.log.push(line);
    }
    if (job.log.length > 400) job.log.splice(0, job.log.length - 400);
  };
  child.stdout.on("data", push);
  child.stderr.on("data", push);
  child.on("error", (err) => {
    job.log.push(String(err));
    job.status = "error";
  });
  child.on("close", (code) => {
    job.status = code === 0 ? "done" : "error";
  });
  return true;
}

// --- Remotion Studio (preview) ------------------------------------------------
let studioChild = null;
const studioRunning = () => Boolean(studioChild && studioChild.exitCode === null);

// --- Routes -------------------------------------------------------------------
app.get("/", (_req, res) => res.sendFile(join(__dirname, "index.html")));

app.get("/api/state", (_req, res) => {
  res.json({
    hasSource: existsSync(join(publicDir, "source.mp4")),
    hasTranscript: existsSync(join(dataDir, "transcript.json")),
    hasRender: existsSync(outFile),
    hasApiKey: Boolean(process.env.OPENAI_API_KEY),
    studioRunning: studioRunning(),
    jobs: Object.fromEntries(Object.entries(jobs).map(([k, v]) => [k, v.status])),
  });
});

app.post("/api/upload-video", videoUpload.single("video"), (_req, res) =>
  res.json({ ok: true })
);

app.post("/api/upload-asset", assetUpload.single("asset"), (req, res) =>
  res.json({ ok: true, filename: req.file.filename })
);

app.post("/api/transcribe", (_req, res) => {
  if (!process.env.OPENAI_API_KEY) {
    // Re-read .env in case the user just added the key.
    try {
      for (const line of readFileSync(join(root, ".env"), "utf8").split("\n")) {
        const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
        if (m) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
      }
    } catch {}
  }
  res.json({ started: startJob("transcribe", [join(root, "scripts", "transcribe.mjs")]) });
});

app.post("/api/render", (_req, res) => {
  res.json({
    started: startJob("render", [
      remotionBin,
      "render",
      "EditedVideo",
      "out/video.mp4",
      "--overwrite",
    ]),
  });
});

app.get("/api/job/:name", (req, res) =>
  res.json(jobs[req.params.name] ?? { status: "idle", log: [] })
);

app.get("/api/transcript", (_req, res) => {
  const p = join(dataDir, "transcript.json");
  if (!existsSync(p)) return res.status(404).json({ error: "No transcript yet" });
  res.type("json").send(readFileSync(p, "utf8"));
});

// graphics.json (array), audio.json (object), ads.json (array) — shared with Studio.
for (const name of ["graphics", "audio", "ads"]) {
  const file = join(dataDir, `${name}.json`);
  app.get(`/api/data/${name}`, (_req, res) =>
    res.type("json").send(readFileSync(file, "utf8"))
  );
  app.post(`/api/data/${name}`, (req, res) => {
    writeFileSync(file, JSON.stringify(req.body, null, 2) + "\n");
    res.json({ ok: true });
  });
}

app.post("/api/studio", (_req, res) => {
  if (!studioRunning()) {
    studioChild = spawn(process.execPath, [remotionBin, "studio", "--no-open"], {
      cwd: root,
      env: process.env,
      stdio: "ignore",
    });
  }
  res.json({ url: "http://localhost:3000" });
});

app.get("/api/download", (_req, res) => {
  if (!existsSync(outFile)) return res.status(404).send("Not rendered yet");
  res.download(outFile);
});

// Clean up the Studio child when the GUI server is stopped.
for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    if (studioRunning()) studioChild.kill();
    process.exit(0);
  });
}

app.listen(PORT, "127.0.0.1", () => {
  console.log(`\n  🎬 Pipeline GUI → http://localhost:${PORT}\n`);
});
