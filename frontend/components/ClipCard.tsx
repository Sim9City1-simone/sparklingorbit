"use client";

import { useState } from "react";
import ShareModal from "./ShareModal";
import CaptionStylePicker, { type CaptionStyle } from "./CaptionStylePicker";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL;

const FORMATS = ["9:16", "1:1", "16:9"] as const;
type Format = (typeof FORMATS)[number];

interface Clip {
  id: string;
  title: string;
  start_time: number;
  end_time: number;
  score: number;
  reason?: string;
}

interface Props {
  clip: Clip;
  videoUrl: string;
  maxScore: number;
}

function formatDuration(start: number, end: number): string {
  const d = Math.round(end - start);
  const m = Math.floor(d / 60);
  const s = d % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

// Aspect ratio padding for each format
const PADDING: Record<Format, string> = {
  "9:16": "177.78%",
  "1:1": "100%",
  "16:9": "56.25%",
};

export default function ClipCard({ clip, videoUrl, maxScore }: Props) {
  const [shareOpen, setShareOpen] = useState(false);
  const [styleOpen, setStyleOpen] = useState(false);
  const [fmt, setFmt] = useState<Format>("9:16");
  const [activeUrl, setActiveUrl] = useState(videoUrl);
  const [reexporting, setReexporting] = useState(false);

  const viralityPct = maxScore > 0 ? Math.min(100, Math.round((clip.score / maxScore) * 100)) : 0;

  async function handleFormatChange(newFmt: Format) {
    if (newFmt === fmt) return;
    setFmt(newFmt);
    await reexport(newFmt, undefined);
  }

  async function handleStyleApply(style: CaptionStyle) {
    await reexport(fmt, style);
  }

  async function reexport(newFmt: Format, style: CaptionStyle | undefined) {
    setReexporting(true);
    try {
      const res = await fetch(`${BACKEND}/reexport`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clip_id: clip.id, fmt: newFmt, style: style ?? null }),
      });
      if (!res.ok) throw new Error("Reexport failed");
      const { url } = await res.json();
      setActiveUrl(`${BACKEND}${url}`);
    } catch {
      // keep current url on error
    } finally {
      setReexporting(false);
    }
  }

  return (
    <>
      <div className="bg-gray-900 rounded-2xl overflow-hidden border border-gray-800 flex flex-col">
        {/* Video */}
        <div className="relative w-full transition-all duration-300" style={{ paddingBottom: PADDING[fmt] }}>
          {reexporting && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 rounded-t-2xl">
              <div className="w-8 h-8 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          <video
            key={activeUrl}
            src={activeUrl}
            controls
            className="absolute inset-0 w-full h-full object-cover"
            preload="metadata"
          />
        </div>

        <div className="p-4 space-y-3">
          {/* Title + duration */}
          <div>
            <p className="font-medium text-sm leading-snug line-clamp-2">{clip.title}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {formatDuration(clip.start_time, clip.end_time)}
            </p>
          </div>

          {/* Virality bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Viralità</span>
              <span className="text-purple-400 font-semibold">{viralityPct}%</span>
            </div>
            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-600 to-pink-500 rounded-full transition-all"
                style={{ width: `${viralityPct}%` }}
              />
            </div>
            {clip.reason && (
              <p className="text-xs text-gray-500 pt-0.5">{clip.reason}</p>
            )}
          </div>

          {/* Format tabs */}
          <div className="flex gap-1">
            {FORMATS.map((f) => (
              <button
                key={f}
                onClick={() => handleFormatChange(f)}
                disabled={reexporting}
                className={`flex-1 py-1 rounded-lg text-xs font-medium transition-colors ${
                  fmt === f
                    ? "bg-purple-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => setStyleOpen(true)}
              className="flex-1 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-xs font-medium transition-colors"
            >
              Caption
            </button>
            <a
              href={activeUrl}
              download={`${clip.title.slice(0, 40)}.mp4`}
              className="flex-1 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-xs font-medium transition-colors text-center"
            >
              Scarica
            </a>
            <button
              onClick={() => setShareOpen(true)}
              className="flex-1 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-sm font-semibold transition-colors"
            >
              Condividi
            </button>
          </div>
        </div>
      </div>

      {shareOpen && (
        <ShareModal clipId={clip.id} defaultTitle={clip.title} onClose={() => setShareOpen(false)} />
      )}
      {styleOpen && (
        <CaptionStylePicker onApply={handleStyleApply} onClose={() => setStyleOpen(false)} />
      )}
    </>
  );
}
