# SparklingOrbit

Opus Clip clone personale — da URL YouTube a short verticali con sottotitoli, pronti per YouTube Shorts / TikTok / Instagram Reels.

## Stack
- **Frontend**: Next.js 15 + Tailwind → Vercel (free)
- **Backend**: FastAPI + yt-dlp + Whisper + FFmpeg → Coolify VPS

---

## Setup Backend (Coolify)

### 1. Configura le variabili d'ambiente
```bash
cp backend/.env.example backend/.env
# Poi riempi i token OAuth
```

### 2. Deploy su Coolify
- Crea un nuovo servizio "Docker Compose" su Coolify
- Punta al repository, seleziona `docker-compose.yml`
- Aggiungi le env vars dalla dashboard Coolify
- Assegna un dominio tipo `sparkling-orbit-api.iamcavalli.net`

### 3. Test backend
```bash
curl https://sparkling-orbit-api.iamcavalli.net/health
# → {"status": "ok"}

curl -X POST https://sparkling-orbit-api.iamcavalli.net/process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
# → {"job_id": "..."}
```

---

## Setup Frontend (Vercel)

```bash
cd frontend
cp .env.local.example .env.local
# Imposta NEXT_PUBLIC_BACKEND_URL con l'URL del tuo backend Coolify

npm install
npm run dev
```

Deploy su Vercel: collega il repo GitHub, imposta la env var `NEXT_PUBLIC_BACKEND_URL`.

---

## Configurare OAuth Social

### YouTube
1. Vai su [Google Cloud Console](https://console.cloud.google.com)
2. Crea un progetto → abilita "YouTube Data API v3"
3. Crea credenziali OAuth 2.0 (tipo Desktop/Web)
4. Ottieni un refresh token con scope `youtube.upload`
5. Inserisci `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` in `.env`

### Instagram
1. Vai su [Meta Developers](https://developers.facebook.com)
2. Crea una app → aggiungi prodotto "Instagram Graph API"
3. Collega un account Creator/Business
4. Genera un token a lunga durata
5. Inserisci `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID` in `.env`

### TikTok
1. Vai su [TikTok Developers](https://developers.tiktok.com)
2. Crea una app → richiedi accesso "Content Posting API"
3. (Approvazione può richiedere qualche giorno)
4. Inserisci `TIKTOK_ACCESS_TOKEN` in `.env`

---

## Note su Whisper
- Il modello `base` è il miglior compromesso velocità/qualità su CPU
- Per video in italiano, Whisper funziona bene nativamente
- Il primo avvio scarica il modello (~140MB) — poi è cached nel container
