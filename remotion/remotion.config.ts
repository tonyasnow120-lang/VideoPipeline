import { Config } from "@remotion/cli/config";

// Rendered videos need a real codec; H.264 is the safe default for MP4.
Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setConcurrency(null); // let Remotion pick based on your CPU

// Overlays use web fonts / emoji; keep chromium happy with these flags.
Config.setChromiumOpenGlRenderer("angle");
