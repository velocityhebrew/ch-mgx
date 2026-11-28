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

## Analysis

When Stockfish is available (the GitHub workflow installs it), every game is
analysed at depth 12:

- real evaluation bar and move-by-move eval chips
- annotations (`??`, `?`, `!`, `!!`)
- a Stockfish-selected turning point and blunder/brilliant badge

If Stockfish is unavailable (for example on a local Windows machine without
the binary), the pipeline falls back to the simulated evaluation path.

## Pipeline

```bash
python daily_runner.py
```

Each run produces up to four YouTube uploads:

1. the full 1080p long-form broadcast (public immediately)
2. the **climax** Short — “Can you find the winning move?”
3. the **opening trap** Short — “Can you spot the opening trap?”
4. the **blunder** Short — “Can you spot the blunder?” (Stockfish-selected)

The **finish** Short — “How did this game end?” — is now a fallback only,
used when a game has no clean opening trap or separate blunder. The data
showed it was the weakest hook.

The Shorts are vertical 9:16, about 16–25 seconds each, and are scheduled
about 1, 3, and 5 hours after the long video. Each one puts the full-game
link near the top of its description.

Outputs in `recordings/`:

- `grandmaster_chess_battle.mp4` — full video
- `thumbnail.png` — YouTube thumbnail
- `chess_subtitles.srt` — captions
- `chapters.json` — chapter timestamps used in the description
- `short_climax.mp4` / `short_opening.mp4` / `short_blunder.mp4` — vertical Shorts
- `short_finish.mp4` — fallback Short when no opening/blunder moment exists
- `short_*_thumbnail.png` — Short cover frames
- `short_*.srt` — Short captions

## GitHub Actions

- Runs daily at 12:00 UTC, or manually from the Actions tab.
- `dry_run=true` generates and archives the video without uploading.
- `upload_youtube=false` skips the YouTube upload.
- The workflow persists the no-repeat game history automatically.
