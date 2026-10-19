# Myanmar Movie Recap Maker (MVP)

## Features
- Upload a video file
- Automatically select short clips from evenly spaced points
- Join selected clips into an MP4 recap
- Optional Burmese text-to-speech narration using gTTS
- Download the final MP4

## Important limitations
- This first version does not understand the movie plot or automatically write an AI summary.
- Clip selection is time-based, not semantic scene detection.
- Burmese TTS availability depends on the upstream gTTS/Google service and internet access.
- Large source files may exceed free hosting memory or processing-time limits.
- Upload only videos you own or have permission to use.

## Render settings
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Environment variables: none required for the MVP

## GitHub files
Upload `app.py`, `requirements.txt`, and `README.md` to the root of a new GitHub repository.
