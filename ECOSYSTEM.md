# Ecosystem Context — For Claude Sessions

## Who I Am
- Name: Tatenda (4kMUDZO)
- Location: Zimbabwe
- Email: tatendawalter62@gmail.com
- YouTube channel: 4kMUDZO (faceless, automated)
- Goal: Build multiple automated income streams using AI + free APIs

## What Exists Already

### YouTube Pipeline (`~/youtube/`)
Fully automated faceless YouTube video pipeline. One command: topic → script → narration → stock footage → subtitles → video → thumbnail → uploaded to YouTube.

**Tech stack (all free):**
- Script gen: Groq API (Llama 3.3 70B)
- Fact checking: Wikipedia API + DuckDuckGo + local research files
- TTS: edge-tts (Microsoft neural voices)
- Stock footage: Pexels API
- Video assembly: MoviePy v2 + ffmpeg
- Thumbnails: Pillow + stock frame extraction
- Upload: YouTube Data API v3 (OAuth 2.0)
- SEO: YouTube autocomplete scraper → title/tag/description optimization
- Engagement: auto-pin comments, AI comment replies, analytics dashboard

**Key files:**
- `pipeline.py` — main pipeline (topic → video → upload)
- `autopilot.py` — daemon mode, batch production, auto-research topics
- `scripts/seo_optimizer.py` — YouTube SEO using autocomplete data
- `scripts/engagement_booster.py` — comments, replies, analytics
- `scripts/fact_checker.py` — Wikipedia/DDG research before scripting
- `scripts/youtube_uploader.py` — OAuth upload + thumbnail
- `config.py` — all settings
- `.env` — API keys (GROQ_API_KEY, PEXELS_API_KEY)
- `client_secret.json` — Google OAuth credentials
- `assets/zim_research.json` — verified Zimbabwean history facts
- `topics.txt` — content calendar with dark history + Zimbabwe topics

**Niches:** dark history/rabbit holes + Zimbabwean stories
**Content output:** `~/youtube/output/videos/` (MP4s), `~/youtube/output/thumbnails/` (PNGs)

**How to run:**
```bash
python3 pipeline.py "Topic" --upload --short     # single video
python3 autopilot.py --videos 5                   # batch
python3 autopilot.py --daemon                     # run forever
python3 scripts/engagement_booster.py full        # engagement
python3 scripts/seo_optimizer.py research --topic "X"  # SEO
```

## Ecosystem Plan — What To Build Next

Each project is a SEPARATE repo/folder. They connect by reading each other's output files, not by importing code.

### 1. TikTok/Reels Repurposer (`~/tiktok/`)
- Reads `~/youtube/output/videos/*_short.mp4`
- Adds TikTok-optimized captions and hooks
- Auto-posts to TikTok + Instagram Reels
- Same content, triple the reach, zero extra work
- **Connect:** reads video files from YouTube output folder

### 2. AI Newsletter (`~/newsletter/`)
- Weekly dark history / Zimbabwe stories newsletter
- Groq writes content, pulls from YouTube scripts
- Host on Substack or Buttondown (free)
- YouTube drives signups, newsletter drives YouTube
- **Connect:** reads `~/youtube/output/*_script.json` for content

### 3. AI Blog / SEO Site (`~/blog/`)
- Long-form articles targeting affiliate keywords
- Groq writes, deploy on Ghost/WordPress
- Amazon Associates for affiliate commissions
- YouTube embeds drive traffic both ways
- **Connect:** can repurpose YouTube scripts into blog posts

### 4. Print-on-Demand (`~/merch/`)
- AI-generated designs for Redbubble/TeePublic
- Zimbabwe/dark history themed merch
- Link from YouTube descriptions
- **Connect:** uses channel branding, links in video descriptions

### 5. YouTube SaaS (`~/youtube-saas/`)
- Package the YouTube pipeline as a web app
- Charge $29-99/month
- The pipeline is already built — just needs a web frontend
- **Connect:** fork of ~/youtube with web UI layer

## Shared Resources
- **API Keys** (in each project's own `.env`):
  - GROQ_API_KEY — free at https://console.groq.com/keys
  - PEXELS_API_KEY — free at https://www.pexels.com/api/
  - Google OAuth — `client_secret.json` from Google Cloud Console
- **Python 3.9+** with pip
- **ffmpeg** (brew install ffmpeg)
- **All projects use Groq for AI** — free tier, 15 RPM

## Rules For Building
1. Each project is its OWN repo with its own `.env`
2. Projects connect through FILE PATHS, not code imports
3. All APIs must be FREE tier — no paid services
4. Security: `.env`, `client_secret.json`, `token.json` always gitignored
5. Every project gets a `requirements.txt` and `.env.example`
6. Commit each major step separately so I can retrace
7. Fact-check everything — use Wikipedia/public sources, don't make stuff up
8. Zimbabwean content must use culturally appropriate visuals and verified facts
9. SEO-optimize everything — use real search data, not guesses
10. Build for automation — everything should run unattended

## Strategy Documents
- `YOUTUBE_STRATEGY.md` — Full growth playbook including:
  - High-velocity niche analysis with RPM/CPM data
  - 30 viral video ideas with hooks and emotional triggers
  - Thumbnail optimization rules for faceless channels
  - 7-beat high-retention script framework with plug-and-play templates
  - Competitive intelligence: what to copy, what to avoid
  - Channel audit checklist
  - Algorithm cheat sheet for 2026

## My Preferences
- I want terse, direct communication — no fluff
- Show me results, not just code
- Commit frequently so I can retrace steps
- Use free tools only
- I'm in Zimbabwe timezone (CAT/UTC+2)
- I want to understand what's happening, explain the "why" briefly
- Security matters — never expose API keys
- I care about output quality — videos should look professional
- Act as YouTube growth strategist, not just engineer
- Every decision should be framed around: will this get more views/subs/money?
