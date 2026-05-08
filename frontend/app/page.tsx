"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "https://tssogk8cw8884okoo4csg04k.178.104.27.55.sslip.io";

const PLATFORM_ICONS: Record<string, string> = {
  youtube: "▶",
  tiktok: "♪",
  instagram: "◈",
};

interface SocialAccount {
  platform: string;
  username: string;
}

interface Creator {
  id: string;
  name: string;
  avatar_url: string | null;
  social_accounts: SocialAccount[];
}

export default function Home() {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [selectedCreator, setSelectedCreator] = useState<Creator | null>(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    fetch(`${BACKEND}/creators`)
      .then((r) => r.json())
      .then(setCreators)
      .catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          creator_id: selectedCreator?.id ?? null,
        }),
      });
      if (!res.ok) throw new Error("Server error");
      const { job_id } = await res.json();
      router.push(`/clips/${job_id}`);
    } catch {
      setError("Errore nell'avvio del job. Controlla che il backend sia attivo.");
      setLoading(false);
    }
  }

  function initials(name: string) {
    return name
      .split(" ")
      .map((w) => w[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 py-12">
      <div className="w-full max-w-2xl space-y-10">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">✨ SparklingOrbit</h1>
          <p className="text-gray-400">
            Incolla un link YouTube e ottieni i tuoi short pronti in minuti
          </p>
        </div>

        {/* Creator selection */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
              Creator
            </h2>
            <div className="flex gap-3">
              <Link
                href="/history"
                className="text-xs text-gray-400 hover:text-white transition-colors"
              >
                Storico
              </Link>
              <Link
                href="/creators"
                className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
              >
                Gestisci →
              </Link>
            </div>
          </div>

          <div className="flex gap-3 flex-wrap">
            {/* "No creator" option */}
            <button
              onClick={() => setSelectedCreator(null)}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm transition-all ${
                selectedCreator === null
                  ? "border-purple-500 bg-purple-600/20 text-white"
                  : "border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-600"
              }`}
            >
              <span className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-xs">
                ✦
              </span>
              Nessuno
            </button>

            {creators.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCreator(c)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm transition-all ${
                  selectedCreator?.id === c.id
                    ? "border-purple-500 bg-purple-600/20 text-white"
                    : "border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-600"
                }`}
              >
                {c.avatar_url ? (
                  <img
                    src={c.avatar_url}
                    alt={c.name}
                    className="w-7 h-7 rounded-full object-cover"
                  />
                ) : (
                  <span className="w-7 h-7 rounded-full bg-purple-700 flex items-center justify-center text-xs font-bold text-white">
                    {initials(c.name)}
                  </span>
                )}
                <span>{c.name}</span>
                {c.social_accounts.length > 0 && (
                  <span className="flex gap-0.5 text-xs text-gray-500">
                    {c.social_accounts.map((a) => (
                      <span key={a.platform}>{PLATFORM_ICONS[a.platform] ?? "·"}</span>
                    ))}
                  </span>
                )}
              </button>
            ))}

            <Link
              href="/creators"
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-dashed border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-400 text-sm transition-all"
            >
              <span className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-base">
                +
              </span>
              Aggiungi
            </Link>
          </div>
        </section>

        {/* URL input */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {selectedCreator && (
            <p className="text-xs text-purple-400 text-center">
              Shorts per <strong>{selectedCreator.name}</strong>
            </p>
          )}
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors"
          >
            {loading ? "Avvio in corso..." : "Genera Shorts"}
          </button>
        </form>

        {error && <p className="text-red-400 text-sm text-center">{error}</p>}

        <p className="text-xs text-gray-600 text-center">
          Il processo richiede 2–5 minuti a seconda della lunghezza del video
        </p>
      </div>
    </main>
  );
}
