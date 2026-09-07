# DAPP Bateman Meme API

Endpoint:

GET /api/meme/bateman?teks1=...&teks2=...&teks3=...

Example:

/api/meme/bateman?teks1=Ketika%20coding%20langsung%20berhasil&teks2=Ternyata%20cuma%20kebetulan&teks3=Error%20lagi%20anjir

The endpoint returns the generated PNG image directly.

Deploy on Render:
1. Upload this project to GitHub.
2. Create a new Web Service on Render.
3. Build: pip install -r requirements.txt
4. Start: uvicorn main:app --host 0.0.0.0 --port $PORT
