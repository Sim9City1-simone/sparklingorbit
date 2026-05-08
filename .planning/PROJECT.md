# SparklingOrbit — Fix & Evolve

## What This Is

SparklingOrbit è un tool personale per la content creation: incolla un URL YouTube, ottieni clip virali pronte da postare. Concorrenti di riferimento: Opus Clip, Vizard.ai.

Il progetto esiste già (backend FastAPI su Coolify, frontend Next.js su Vercel) ma **non ha mai funzionato in produzione**. L'obiettivo immediato è farlo funzionare, poi aggiungere le feature mancanti per renderlo davvero utile.

## Core Value

**URL YouTube → clip video in produzione, in autonomia, senza intervento manuale.**

## Context

### Stack (già deployato)

| Layer | Tecnologia | URL / Path |
|-------|-----------|------------|
| Frontend | Next.js 14 + Tailwind | Vercel — sparklingorbit.com (o simile) |
| Backend | FastAPI + Python 3.11 | `https://sparkling-orbit-api.iamcavalli.net` |
| DB | SQLite | `/data/sparkling.db` nel container |
| Temp files | Filesystem | `/data/clips` nel container |
| Deploy | Coolify (Docker) | `ssh root@cooli.iamcavalli.net` |

### Pipeline attuale (jobs.py)

1. **Phase 1–2 — Trascrizione**: `youtube-transcript-api` fetch captions dirette (no download). Fallback: yt-dlp audio → Groq Whisper large-v3 → faster-whisper CPU.
2. **Phase 3 — Scoring**: `scorer.py` trova i 5 segmenti migliori.
3. **Phase 4 — Editing**: yt-dlp scarica solo il segmento → `editor.py` renderizza con sottotitoli.

### Bug bloccanti in produzione (identificati)

| Bug | Causa | Impatto |
|-----|-------|---------|
| Cookie YouTube scaduti | `YOUTUBE_COOKIES_B64` in Coolify con cookie expirata | Fallback audio fallisce, job va in errore |
| yt-dlp usa `[youtube+oauth2]` | Configurazione cookie/oauth2 non corretta nel container | Tutti i video senza captions falliscono |

### Infrastruttura verificata

- Backend risponde correttamente (200 su /process, /jobs, /creators)
- Frontend su Vercel chiama correttamente il backend Coolify
- Container running, nessun crash loop
- `GROQ_API_KEY` e `YOUTUBE_COOKIES_B64` impostati in Coolify (ma cookie scaduta)

## Requirements

### Validated

- ✓ Backend FastAPI deployato e raggiungibile — esistente
- ✓ Frontend Next.js su Vercel — esistente
- ✓ Pipeline trascrizione (youtube-transcript-api + Groq + Whisper) — esistente
- ✓ Pipeline scoring segmenti — esistente
- ✓ Pipeline editing clip — esistente
- ✓ Gestione job asincrona (BackgroundTasks) — esistente
- ✓ CRUD creators + social accounts — esistente

### Active

- [ ] **CORE-01**: Cookie YouTube aggiornati → yt-dlp scarica audio senza errore "not a bot"
- [ ] **CORE-02**: Tutti i job completano senza errore (test su 5 URL diversi)
- [ ] **CORE-03**: Cookie management robusto — soluzione che non richieda update manuale mensile
- [ ] **TRANSCRIPT-01**: Navigazione interattiva testo ↔ video (stile Vizard.ai) — click su paragrafo → jump al timestamp
- [ ] **CLIP-01**: Re-export clip con formato e stile diverso (già endpoint `/reexport` ma non testato)
- [ ] **SCHEDULE-01**: Calendario editoriale — visualizza e pianifica quando postare ogni clip
- [ ] **SOCIAL-01**: Scheduling automatico post su Instagram/TikTok/YouTube Shorts
- [ ] **ANALYTICS-01**: Tracking views e performance dei reel postati

### Out of Scope

- Supporto multi-utente / SaaS — tool personale, un solo utente
- Login / autenticazione utente — non necessario (tool privato)
- Billing / subscription — uso personale
- App mobile — web è sufficiente

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| YouTube cookie vs OAuth2 permanente vs PO Token | Cookie scade ogni 1-2 mesi, OAuth2 più stabile, PO Token sperimentale | Da valutare in Phase 1 |
| Coolify vs alternative deploy | Già in uso, funziona, non cambiare | Coolify — mantieni |
| SQLite vs PostgreSQL | Uso personale, un solo utente, nessun problema di concorrenza | SQLite — mantieni |
| youtube-transcript-api (zero download) per captions | Evita bot detection su Phase 1-2 | Confermato — mantieni |

## Evolution

Questo documento evolve ad ogni phase transition e milestone.

**Dopo ogni phase transition** (via `/gsd-transition`):
1. Requirements invalidati? → Sposta in Out of Scope con motivazione
2. Requirements validati? → Sposta in Validated con riferimento alla phase
3. Nuovi requirements emersi? → Aggiungi in Active
4. Decisioni da loggare? → Aggiungi in Key Decisions
5. "What This Is" ancora accurato? → Aggiorna se necessario

**Dopo ogni milestone** (via `/gsd-complete-milestone`):
1. Review completa di tutte le sezioni
2. Core Value check — ancora la priorità giusta?
3. Audit Out of Scope — le motivazioni sono ancora valide?
4. Aggiorna Context con stato attuale

---
*Last updated: 2026-05-08 — initialization*
