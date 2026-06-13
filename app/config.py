from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
WORKSPACE_DIR = DATA_DIR / "workspace"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
DB_PATH = DATA_DIR / "faceless.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

for d in [DATA_DIR, OUTPUTS_DIR, WORKSPACE_DIR, MUSIC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ART_STYLE_DESCRIPTORS = {
    "anime":        "dramatic anime illustration, Studio Ghibli-inspired, rich linework, vibrant colors",
    "comic":        "American comic book art, bold ink lines, flat cel colors, dynamic composition",
    "realism":      "photorealistic digital painting, cinematic lighting, ultra-detailed",
    "watercolor":   "loose expressive watercolor, soft wet edges, painterly brushwork",
    "dark_fantasy": "dark fantasy oil painting, dramatic shadows, gothic atmosphere, detailed",
    "minimalist":   "clean vector illustration, geometric shapes, limited palette, modern flat design",
    "retro":        "retro 1970s poster illustration, grain texture, muted earthy palette",
    "cinematic":    "cinematic concept art, dramatic key lighting, film-still aesthetic, high contrast",
}

NICHES = [
    "History", "True Crime", "Science & Space", "Psychology",
    "Nature & Wildlife", "Philosophy", "Mythology",
    "Unsolved Mysteries", "Technology", "Finance & Money", "Custom"
]

TIMEZONES = [
    "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Paris", "Europe/Berlin",
    "Asia/Tokyo", "Asia/Singapore", "Australia/Sydney"
]
