# Chess AI Grandmaster: Dual-Character Daily YouTube Automation

An automated, broadcast-ready Chess video and thumbnail generation suite powered by **Stockfish 19** (3600+ ELO), **Python-Chess**, and **Microsoft Neural Edge-TTS**.

---

## Features

* **Dual-Character Grandmaster Dialogue:** Two distinct AI personas banter and explain their tactical ideas on every move:
  * **White:** GM Alexander "The Tactician" (`en-US-GuyNeural`) — aggressive, tactical kingside attacker.
  * **Black:** GM Victor "The Iron Defense" (`en-US-ChristopherNeural`) — deep, analytical Sicilian counter-puncher.
* **Red Tactical Move Arrows:** Dynamic vector arrows showing exactly which piece moved where, highlights checks, and illustrates tactical sacrifices.
* **High-Contrast Circular Avatars:** Sleek circular medallions with glowing cyan and gold rings for crystal-clear player identification.
* **Live Left-Side Move Log & HUD:** Real-time scrolling move history with ELO ratings, engine evaluation badges (`+0.3`, `+1.8`, `+7.5`), and ticking 10-minute rapid clocks.
* **High-Impact YouTube Thumbnail Generator:** Automatically takes a snapshot at the mid-game tactical climax with bold badges (`!! BRILLIANT MOVE`) and red arrows ready for YouTube upload.
* **Daily Automation & GitHub Actions:** Pre-configured workflow (`.github/workflows/daily_chess_video.yml`) that can run automatically on a cloud schedule and post daily videos to YouTube.

---

## Folder Structure

```
D:\E agy cli\E bots\E gaming\chess-ai-grandmaster\
├── .github\workflows\
│   └── daily_chess_video.yml    # Daily cloud automation workflow
├── engine\
│   └── stockfish\               # Stockfish 19 Universal Windows binary
├── recordings\
│   ├── grandmaster_chess_battle.mp4  # Master 1080p 60fps match video
│   ├── thumbnail.png                 # YouTube thumbnail at game climax
│   └── chess_subtitles.srt           # Synced dialogue subtitles
├── board_renderer.py            # 1080p broadcast renderer with red arrows & avatars
├── chess_gameplay.py            # Master moves, tactical analysis & character dialogue
├── match_narrator.py            # Dual-voice Edge-TTS neural engine
├── thumbnail_generator.py       # High-CTR YouTube thumbnail generator
├── generate_chess_video.py      # Master video compiler & FFmpeg pipeline
├── youtube_uploader.py          # YouTube Data API v3 uploader
├── daily_runner.py              # Automated daily orchestration script
├── start_chess.bat              # 1-click Windows launcher
└── README.md
```

---

## How to Run Locally

### 1-Click Launch:
Double-click:
```bat
start_chess.bat
```
Or run from PowerShell:
```powershell
python "D:\E agy cli\E bots\E gaming\chess-ai-grandmaster\generate_chess_video.py"
```

The finished video and thumbnail will be saved in `recordings/`.

---

## How to Push to GitHub & Automate Daily YouTube Uploads

1. Initialize Git repository and commit:
```powershell
cd "D:\E agy cli\E bots\E gaming\chess-ai-grandmaster"
git init
git add .
git commit -m "Grandmaster Chess AI Video Generator"
```

2. Link to your GitHub repository:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/chess-ai-automation.git
git branch -M main
git push -u origin main
```

3. Enable Daily Cloud Publishing:
   * Go to your repository on GitHub $\rightarrow$ **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
   * Add your YouTube API credentials (`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`).
   * GitHub Actions will automatically generate and upload a new match video every single day!
