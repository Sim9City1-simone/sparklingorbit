"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) throw new Error("Server error");
      const { job_id } = await res.json();
      router.push(`/clips/${job_id}`);
    } catch {
      setError("Errore nell'avvio del job. Controlla che il backend sia attivo.");
      setLoading(false);
    }
  }

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-xl text-center space-y-8">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            ✨ SparklingOrbit
          </h1>
          <p className="mt-2 text-gray-400">
            Incolla un link YouTube e ottieni i tuoi short pronti in minuti
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
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

        {error && (
          <p className="text-red-400 text-sm">{error}</p>
        )}

        <p className="text-xs text-gray-600">
          Il processo richiede 2–5 minuti a seconda della lunghezza del video
        </p>
      </div>
    </main>
  );
}
