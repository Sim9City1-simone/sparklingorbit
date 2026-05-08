# Roadmap: SparklingOrbit Fix & Evolve

## Overview

The project exists and is deployed but has never worked in production due to expired YouTube cookies. The roadmap follows three natural delivery boundaries: first make it work (fix the blocking bugs), then make it useful (interactive transcript and timeline editor), then close the content loop (schedule, post, and track clips automatically).

## Phases

- [ ] **Phase 1: Production Fix** - Repair the broken YouTube auth so jobs complete end-to-end for the first time
- [ ] **Phase 2: Interactive Editor** - Add transcript navigation and timeline trimming so users control every clip before export
- [ ] **Phase 3: Publish & Track** - Schedule clips, auto-post to social platforms, and surface performance data

## Phase Details

### Phase 1: Production Fix
**Goal**: Users can submit a YouTube URL and receive processed clips without any manual intervention on the server
**Mode:** mvp
**Depends on**: Nothing (first phase — brownfield fix)
**Requirements**: CORE-01, CORE-02, CORE-03
**Success Criteria** (what must be TRUE):
  1. User submits any YouTube URL and the job completes without a "Sign in to confirm you're not a bot" error
  2. 5 different YouTube URLs (mix of videos with and without captions) all reach status "complete" without manual server action
  3. The authentication solution does not require a manual cookie update more often than every 6 months
  4. Existing clips and creators data in the UI remain intact after the fix is applied
**Plans**: TBD

### Phase 2: Interactive Editor
**Goal**: Users can review the full transcript and fine-tune clip boundaries directly in the browser before exporting
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: TRANSCRIPT-01, EDITOR-01
**Success Criteria** (what must be TRUE):
  1. User clicks any paragraph in the transcript panel and the video player jumps to the corresponding timestamp
  2. User drags start and end markers on the timeline editor to set custom in/out points for a clip
  3. User re-exports the trimmed clip and receives a new video file reflecting the custom boundaries
**Plans**: TBD
**UI hint**: yes

### Phase 3: Publish & Track
**Goal**: Users can schedule clips for publication, have them posted automatically, and see real view counts from social platforms
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: SCHEDULE-01, SOCIAL-01, ANALYTICS-01
**Success Criteria** (what must be TRUE):
  1. User assigns a publication date and time to a clip and sees it appear on the editorial calendar view
  2. At the scheduled time, the clip is automatically posted to at least one connected platform (Instagram Reels or TikTok) without user action
  3. For each posted clip, the UI shows the current view count fetched from the platform API
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Production Fix | 0/TBD | Not started | - |
| 2. Interactive Editor | 0/TBD | Not started | - |
| 3. Publish & Track | 0/TBD | Not started | - |
