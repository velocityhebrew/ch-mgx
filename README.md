# Chess Magix

Daily 1080p / 60fps grandmaster chess videos with AI commentary, a broadcast-style
board UI, custom thumbnails, chapters, captions, and automatic publishing to
YouTube and Facebook.

## Game selection

- **Primary — unlimited dynamic pool:** recent decisive standard games from active
  elite Chess.com players (`game_source.py`). Games are filtered to 78–100 plies
  (roughly 7–9 minutes at the current narration pace) and 2400+ ratings.
- **Fallback — curated library:** the 30 historical masterpieces in
  `grandmaster_database.py`, used only if the dynamic source is unavailable.
- **No repeats:** every selected game is written to `used_games.json`. The GitHub
  Actions workflow commits that file back to the repository after each run.
- Set `GAME_SOURCE=auto` (default), `GAME_SOURCE=dynamic`, or
  `GAME_SOURCE=curated` to control the source.

## Pipeline

```bash
python daily_runner.py
```

Each run produces two YouTube uploads:

1. the full 1080p long-form broadcast
2. a vertical 9:16 **Short** built from the game's climax, with a hook,
   the answer, and a link to the full video

Outputs in `recordings/`:

- `grandmaster_chess_battle.mp4` — full video
- `thumbnail.png` — YouTube thumbnail
- `chess_subtitles.srt` — captions
- `chapters.json` — chapter timestamps used in the description
- `short.mp4` — vertical Short
- `short_thumbnail.png` — Short cover frame
- `short.srt` — Short captions

## GitHub Actions

- Runs daily at 12:00 UTC, or manually from the Actions tab.
- `dry_run=true` generates and archives the video without uploading.
- `upload_youtube=false` skips the YouTube upload.
- The workflow persists the no-repeat game history automatically.
