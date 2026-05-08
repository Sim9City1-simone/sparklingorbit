"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ClipCard from "@/components/ClipCard";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "https://tssogk8cw8884okoo4csg04k.178.104.27.55.sslip.io";

const STEPS = [
  { key: "downloading", label: "Download video" },
  { key: "transcribing", label: "Trascrizione audio" },
  { key: "scoring", label: "Analisi momenti migliori" },
  { key: "editing", label: "Generazione clip" },
  { key: "done", label: "Completato" },
];

const STEP_KEYS = STEPS.map((s) => s.key);

interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

interface Clip {
  id: string;
  title: string;
  start_time: number;
  end_time: number;
  score: number;
  reason?: string;
  file_path: string;
}

interface JobData {
  id: string;
  status: string;
  error: string | null;
  clips: Clip[];
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export default function ClipsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobData | null>(null);
  const [transcript, setTranscript] = useState<TranscriptSegment[] | null>(null);
  const [transcriptOpen, setTranscriptOpen] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const res = await fetch(`${BACKEND}/jobs/${jobId}`);
        if (!res.ok) return;
        const data: JobData = await res.json();
        setJob(data);
        if (data.status !== "done" && data.status !== "error") {
          setTimeout(poll, 3000);
        }
      } catch {
        setTimeout(poll, 5000);
      }
    };

    poll();
  }, [jobId]);

  async function loadTranscript() {
    if (transcript) { setTranscriptOpen((o: boolean) => !o); return; }
    try {
      const res = await fetch(`${BACKEND}/jobs/${jobId}/transcript`);
      if (!res.ok) return;
      const data = await res.json();
      setTranscript(data.segments);
      setTranscriptOpen(true);
    } catch { /* transcript not ready */ }
  }

  const clipUrl = (filePath: string) => {
    const parts = filePath.split("/data/clips/");
    if (parts.length < 2) return "";
    return `${BACKEND}/clips/${parts[1]}`;
  };

  const maxScore = job ? Math.max(...job.clips.map((c: Clip) => c.score), 1) : 1;
  const currentStepIdx = job ? STEP_KEYS.indexOf(job.status) : -1;

  if (!job) {
    return (
      <main className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400 animate-pulse">Caricamento...</p>
      </main>
    );
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-12 space-y-10">
      {/* Header */}
      <div className="text-center space-y-4">
        <a href="/" className="inline-block text-3xl font-bold hover:opacity-80 transition-opacity">
          ✨ SparklingOrbit
        </a>

        {/* Step progress */}
        {job.status !== "done" && job.status !== "error" && (
          <div className="flex items-center justify-center gap-1 flex-wrap">
            {STEPS.slice(0, -1).map((step, idx) => {
              const done = currentStepIdx > idx;
              const active = currentStepIdx === idx;
              return (
                <div key={step.key} className="flex items-center gap-1">
                  <div
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      active
                        ? "bg-purple-600 text-white"
                        : done
                        ? "bg-gray-700 text-gray-300"
                        : "bg-gray-800 text-gray-600"
                    }`}
                  >
                    {done ? "✓" : active ? <span className="animate-pulse">●</span> : "○"}
                    {step.label}
                  </div>
                  {idx < STEPS.length - 2 && <span className="text-gray-700">›</span>}
                </div>
              );
            })}
          </div>
        )}

        {job.status === "done" && (
          <p className="text-green-400 text-sm font-medium">
            ✓ {job.clips.length} short{job.clips.length > 1 ? "s" : ""} pronti
          </p>
        )}

        {job.status === "error" && (
          <p className="text-red-400 text-sm max-w-lg mx-auto">{job.error}</p>
        )}
      </div>

      {/* Transcript toggle */}
      {(job.status === "done" || job.status === "editing" || transcript) && (
        <div className="border border-gray-800 rounded-2xl overflow-hidden">
          <button
            onClick={loadTranscript}
            className="w-full flex justify-between items-center px-5 py-3 text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-800/50 transition-colors"
          >
            <span>Trascrizione</span>
            <span className="text-gray-600">{transcriptOpen ? "▲" : "▼"}</span>
          </button>
          {transcriptOpen && transcript && (
            <div className="px-5 pb-4 max-h-56 overflow-y-auto space-y-1 bg-gray-900/50">
              {transcript.map((seg, i) => (
                <div key={i} className="flex gap-3 text-sm">
                  <span className="text-gray-600 font-mono shrink-0 pt-0.5">
                    {formatTime(seg.start)}
                  </span>
                  <p className="text-gray-300 leading-relaxed">{seg.text.trim()}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Clips grid */}
      {job.clips.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-200">
            {job.clips.length} short{job.clips.length > 1 ? "s" : ""}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {job.clips.map((clip) => (
              <ClipCard
                key={clip.id}
                clip={clip}
                videoUrl={clipUrl(clip.file_path)}
                maxScore={maxScore}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
