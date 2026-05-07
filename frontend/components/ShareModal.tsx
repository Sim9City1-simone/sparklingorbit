"use client";

import { useState } from "react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

const PLATFORMS = [
  { id: "youtube", label: "YouTube Shorts", emoji: "▶️" },
  { id: "tiktok", label: "TikTok", emoji: "🎵" },
  { id: "instagram", label: "Instagram Reels", emoji: "📷" },
];

interface Props {
  clipId: string;
  defaultTitle: string;
  onClose: () => void;
}

export default function ShareModal({ clipId, defaultTitle, onClose }: Props) {
  const [platform, setPlatform] = useState("youtube");
  const [title, setTitle] = useState(defaultTitle);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ url?: string; error?: string } | null>(null);

  async function handleShare() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${BACKEND}/share`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clip_id: clipId, platform, title, description }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Errore sconosciuto");
      setResult({ url: data.url });
    } catch (e: unknown) {
      setResult({ error: e instanceof Error ? e.message : "Errore sconosciuto" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-md p-6 space-y-5 border border-gray-800">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold">Condividi clip</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl">✕</button>
        </div>

        <div className="grid grid-cols-3 gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlatform(p.id)}
              className={`py-2 px-3 rounded-xl text-sm font-medium transition-colors ${
                platform === p.id
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {p.emoji} {p.label}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titolo"
            className="w-full px-4 py-2 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-sm"
          />
          {platform !== "tiktok" && (
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descrizione (opzionale)"
              rows={2}
              className="w-full px-4 py-2 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-sm resize-none"
            />
          )}
        </div>

        {result?.url && (
          <div className="bg-green-900/40 border border-green-700 rounded-xl p-3 text-sm text-green-300">
            Pubblicato!{" "}
            <a href={result.url} target="_blank" rel="noopener noreferrer" className="underline">
              Apri link
            </a>
          </div>
        )}

        {result?.error && (
          <p className="text-red-400 text-sm">{result.error}</p>
        )}

        <button
          onClick={handleShare}
          disabled={loading || !title.trim()}
          className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors"
        >
          {loading ? "Pubblicazione..." : "Pubblica ora"}
        </button>
      </div>
    </div>
  );
}
