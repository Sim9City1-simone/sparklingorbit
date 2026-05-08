# Requirements — SparklingOrbit Fix & Evolve

## v1 Requirements

### Core Fix

- [ ] **CORE-01**: Il job processa un video YouTube e scarica l'audio senza errore "Sign in to confirm you're not a bot"
- [ ] **CORE-02**: 5 URL YouTube diversi (con e senza captions) completano il job senza errore
- [ ] **CORE-03**: La soluzione cookie/auth non richiede aggiornamento manuale più spesso di ogni 6+ mesi (PO Token, OAuth2 permanente, o alternativa a yt-dlp)

### Transcript & Editor

- [ ] **TRANSCRIPT-01**: Click su un segmento del trascritto nell'UI → il video jumpa al timestamp corrispondente
- [ ] **EDITOR-01**: Timeline editor nell'UI — l'utente può trascinare i marcatori di inizio/fine per ritagliare la clip manualmente prima del re-export

### Content & Social

- [ ] **SCHEDULE-01**: Calendario editoriale — visualizza le clip pianificate su un calendario, può assegnare una data/ora di pubblicazione a ogni clip
- [ ] **SOCIAL-01**: Post automatico su almeno una piattaforma (Instagram Reels o TikTok) alla data/ora pianificata
- [ ] **ANALYTICS-01**: Per ogni clip postata, mostra il numero di views corrente (fetched dall'API della piattaforma)

## v2 Requirements (deferred)

- Re-export clip con formato diverso (9:16, 1:1, 16:9) — endpoint `/reexport` già esiste, manca solo UI
- Player video integrato (ora il download è l'unica opzione)
- Supporto scheduling su YouTube Shorts
- Suggerimenti AI per titolo/caption del post
- Notifica (email/push) quando il job è completato

## Out of Scope

- Multi-utente / SaaS — tool personale, un solo utente
- Autenticazione utente — non necessario (tool privato)
- Billing / subscription — uso personale
- App mobile — web è sufficiente
- Editor video frame-by-frame — troppo complesso, timeline è sufficiente
- Integrazione con Opus Clip / Vizard.ai — tool indipendente

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| CORE-01 | Phase 1 | Pending |
| CORE-02 | Phase 1 | Pending |
| CORE-03 | Phase 1 | Pending |
| TRANSCRIPT-01 | Phase 2 | Pending |
| EDITOR-01 | Phase 2 | Pending |
| SCHEDULE-01 | Phase 3 | Pending |
| SOCIAL-01 | Phase 3 | Pending |
| ANALYTICS-01 | Phase 3 | Pending |
