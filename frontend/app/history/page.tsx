"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "https://tssogk8cw8884okoo4csg04k.178.104.27.55.sslip.io";

interface Job {
  id: string;
  youtube_url: string;
  status: string;
  created_at: string;
  clips_count: number;
  creator_id: string | null;
  creator_name: string | null;
  creator_avatar: string | null;
}

interface Group {
  creatorId: string | null;
  creatorName: string;
  creatorAvatar: string | null;
  jobs: Job[];
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  done:         { label: "Completato", color: "text-green-400 bg-green-950/40 border-green-800" },
  error:        { label: "Errore",     color: "text-red-400 bg-red-950/40 border-red-800" },
  pending:      { label: "In coda",    color: "text-gray-400 bg-gray-800/40 border-gray-700" },
  downloading:  { label: "Download",   color: "text-blue-400 bg-blue-950/40 border-blue-800" },
  transcribing: { label: "Trascrizione", color: "text-purple-400 bg-purple-950/40 border-purple-800" },
  scoring:      { label: "Analisi",    color: "text-yellow-400 bg-yellow-950/40 border-yellow-800" },
  editing:      { label: "Montaggio",  color: "text-orange-400 bg-orange-950/40 border-orange-800" },
};

function getYouTubeId(url: string): string | null {
  const m = url.match(/(?:v=|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})/);
  return m ? m[1] : null;
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("it-IT", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export default function HistoryPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND}/jobs`);
      if (!r.ok) return;
      const jobs: Job[] = await r.json();

      const map = new Map<string, Group>();
      for (const job of jobs) {
        const key = job.creator_id ?? "__none__";
        if (!map.has(key)) {
          map.set(key, {
            creatorId: job.creator_id,
            creatorName: job.creator_name ?? "Nessun creator",
            creatorAvatar: job.creator_avatar,
            jobs: [],
          });
        }
        map.get(key)!.jobs.push(job);
      }

      // "Nessun creator" last
      const sorted = [...map.values()].sort((a, b) =>
        a.creatorId === null ? 1 : b.creatorId === null ? -1 : a.creatorName.localeCompare(b.creatorName)
      );
      setGroups(sorted);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function deleteJob(jobId: string) {
    if (!confirm("Eliminare questo job e tutti i clip generati?")) return;
    setDeleting((s) => new Set(s).add(jobId));
    try {
      await fetch(`${BACKEND}/jobs/${jobId}`, { method: "DELETE" });
      await load();
    } finally {
      setDeleting((s) => { const n = new Set(s); n.delete(jobId); return n; });
    }
  }

  const totalJobs = groups.reduce((sum, g) => sum + g.jobs.length, 0);

  return (
    <main className="max-w-4xl mx-auto px-4 py-12 space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-2xl font-bold hover:opacity-80 transition-opacity">
            ✨ SparklingOrbit
          </Link>
          <p className="text-gray-400 text-sm mt-1">
            Storico — {totalJobs} job{totalJobs !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-4 text-sm text-gray-400">
          <Link href="/creators" className="hover:text-white transition-colors">Creator</Link>
          <Link href="/" className="hover:text-white transition-colors">← Home</Link>
        </div>
      </div>

      {loading && (
        <p className="text-gray-500 text-sm text-center py-16">Caricamento...</p>
      )}

      {!loading && totalJobs === 0 && (
        <div className="text-center py-16 space-y-3">
          <p className="text-gray-400">Nessun job ancora.</p>
          <Link href="/" className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
            Genera i tuoi primi shorts →
          </Link>
        </div>
      )}

      {groups.map((group) => (
        <section key={group.creatorId ?? "__none__"} className="space-y-4">
          {/* Creator header */}
          <div className="flex items-center gap-3">
            {group.creatorId ? (
              group.creatorAvatar ? (
                <img src={group.creatorAvatar} alt={group.creatorName}
                  className="w-8 h-8 rounded-full object-cover" />
              ) : (
                <span className="w-8 h-8 rounded-full bg-purple-700 flex items-center justify-center text-xs font-bold">
                  {initials(group.creatorName)}
                </span>
              )
            ) : (
              <span className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-base">✦</span>
            )}
            <h2 className="font-semibold text-white">{group.creatorName}</h2>
            <span className="text-xs text-gray-500">{group.jobs.length} job{group.jobs.length !== 1 ? "s" : ""}</span>
          </div>

          {/* Job cards */}
          <div className="grid gap-3 sm:grid-cols-2">
            {group.jobs.map((job) => {
              const ytId = getYouTubeId(job.youtube_url);
              const thumb = ytId ? `https://img.youtube.com/vi/${ytId}/mqdefault.jpg` : null;
              const status = STATUS_LABELS[job.status] ?? { label: job.status, color: "text-gray-400 bg-gray-800/40 border-gray-700" };

              return (
                <div key={job.id}
                  className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden flex flex-col">
                  {/* Thumbnail */}
                  {thumb ? (
                    <div className="relative w-full aspect-video bg-gray-800">
                      <img src={thumb} alt="thumbnail" className="w-full h-full object-cover" />
                      <span className={`absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full border ${status.color}`}>
                        {status.label}
                      </span>
                    </div>
                  ) : (
                    <div className="w-full aspect-video bg-gray-800 flex items-center justify-center">
                      <span className="text-gray-600 text-sm">Nessuna anteprima</span>
                    </div>
                  )}

                  {/* Info */}
                  <div className="p-4 flex-1 flex flex-col gap-3">
                    <p className="text-xs text-gray-500 truncate">{job.youtube_url}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{formatDate(job.created_at)}</span>
                      <span className="text-purple-400 font-medium">
                        {job.clips_count} clip{job.clips_count !== 1 ? "s" : ""}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-auto">
                      {job.status === "done" && job.clips_count > 0 ? (
                        <Link
                          href={`/clips/${job.id}`}
                          className="flex-1 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-center transition-colors"
                        >
                          Vedi clips →
                        </Link>
                      ) : (
                        <div className="flex-1 py-2 rounded-xl bg-gray-800 text-xs text-gray-600 text-center">
                          {job.status === "error" ? "Errore" : "In elaborazione..."}
                        </div>
                      )}
                      <button
                        onClick={() => deleteJob(job.id)}
                        disabled={deleting.has(job.id)}
                        className="px-3 py-2 rounded-xl bg-gray-800 hover:bg-red-900/40 text-gray-500 hover:text-red-400 text-xs transition-colors disabled:opacity-40"
                      >
                        {deleting.has(job.id) ? "..." : "✕"}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </main>
  );
}
