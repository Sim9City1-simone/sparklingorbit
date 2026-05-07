"use client";

import { useState } from "react";

export interface CaptionStyle {
  highlight_color: string;
  text_color: string;
  outline_color: string;
  font_size: number;
  position: "bottom" | "center" | "top";
  bold: boolean;
  uppercase: boolean;
  outline_size: number;
  shadow_size: number;
  words_per_chunk: number;
  border_style: number;
  preset?: string;
}

const PRESETS: { id: string; label: string; emoji: string; desc: string; style: CaptionStyle }[] = [
  {
    id: "default",
    label: "Default",
    emoji: "✦",
    desc: "Giallo classico",
    style: {
      highlight_color: "FFFF00", text_color: "FFFFFF", outline_color: "000000",
      font_size: 56, bold: true, uppercase: false, outline_size: 3, shadow_size: 1,
      words_per_chunk: 3, position: "bottom", border_style: 1,
    },
  },
  {
    id: "tiktok",
    label: "TikTok",
    emoji: "♪",
    desc: "Bold maiuscolo",
    style: {
      highlight_color: "FFFF00", text_color: "FFFFFF", outline_color: "000000",
      font_size: 62, bold: true, uppercase: true, outline_size: 2.5, shadow_size: 1.5,
      words_per_chunk: 3, position: "bottom", border_style: 1,
    },
  },
  {
    id: "mrbeast",
    label: "MrBeast",
    emoji: "⚡",
    desc: "Box giallo 2 parole",
    style: {
      highlight_color: "FFFFFF", text_color: "FFFF00", outline_color: "000000",
      font_size: 68, bold: true, uppercase: true, outline_size: 3, shadow_size: 0,
      words_per_chunk: 2, position: "bottom", border_style: 3,
    },
  },
  {
    id: "minimal",
    label: "Minimal",
    emoji: "◦",
    desc: "Sottile blu",
    style: {
      highlight_color: "00BFFF", text_color: "FFFFFF", outline_color: "000000",
      font_size: 50, bold: false, uppercase: false, outline_size: 1.5, shadow_size: 1,
      words_per_chunk: 4, position: "bottom", border_style: 1,
    },
  },
];

function HexColorInput({ label, value, onChange }: {
  label: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-gray-400 w-24 shrink-0">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={`#${value}`}
          onChange={(e) => onChange(e.target.value.replace("#", "").toUpperCase())}
          className="w-7 h-7 rounded cursor-pointer bg-transparent border-0"
        />
        <span className="text-xs font-mono text-gray-500">#{value}</span>
      </div>
    </div>
  );
}

interface Props {
  onApply: (style: CaptionStyle) => void;
  onClose: () => void;
}

export default function CaptionStylePicker({ onApply, onClose }: Props) {
  const [selected, setSelected] = useState<string>("default");
  const [style, setStyle] = useState<CaptionStyle>(PRESETS[0].style);

  function selectPreset(id: string) {
    const p = PRESETS.find((p) => p.id === id);
    if (!p) return;
    setSelected(id);
    setStyle(p.style);
  }

  function patch(partial: Partial<CaptionStyle>) {
    setSelected("custom");
    setStyle((s) => ({ ...s, ...partial }));
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4 overflow-y-auto py-8">
      <div className="bg-gray-900 rounded-2xl w-full max-w-sm p-6 space-y-5 border border-gray-800">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold">Stile Caption</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl">✕</button>
        </div>

        {/* Preset cards */}
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => selectPreset(p.id)}
              className={`p-3 rounded-xl border text-left transition-all ${
                selected === p.id
                  ? "border-purple-500 bg-purple-600/20"
                  : "border-gray-700 bg-gray-800/50 hover:border-gray-600"
              }`}
            >
              <div className="text-xl mb-1">{p.emoji}</div>
              <div className="text-sm font-semibold text-white">{p.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-800 pt-4 space-y-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Personalizza</p>

          {/* Colors */}
          <div className="space-y-2.5">
            <HexColorInput label="Parola attiva" value={style.highlight_color}
              onChange={(v) => patch({ highlight_color: v })} />
            <HexColorInput label="Testo" value={style.text_color}
              onChange={(v) => patch({ text_color: v })} />
            <HexColorInput label="Contorno" value={style.outline_color}
              onChange={(v) => patch({ outline_color: v })} />
          </div>

          {/* Font size */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Grandezza testo</span>
              <span className="font-mono">{style.font_size}px</span>
            </div>
            <input type="range" min={36} max={84} value={style.font_size}
              onChange={(e) => patch({ font_size: Number(e.target.value) })}
              className="w-full accent-purple-500" />
          </div>

          {/* Words per chunk */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Parole per blocco</span>
              <span className="font-mono">{style.words_per_chunk}</span>
            </div>
            <input type="range" min={1} max={6} value={style.words_per_chunk}
              onChange={(e) => patch({ words_per_chunk: Number(e.target.value) })}
              className="w-full accent-purple-500" />
          </div>

          {/* Position */}
          <div className="space-y-1.5">
            <p className="text-xs text-gray-400">Posizione</p>
            <div className="flex gap-1.5">
              {(["bottom", "center", "top"] as const).map((pos) => (
                <button key={pos} onClick={() => patch({ position: pos })}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    style.position === pos
                      ? "bg-purple-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}>
                  {pos}
                </button>
              ))}
            </div>
          </div>

          {/* Toggles */}
          <div className="flex gap-2">
            <button onClick={() => patch({ uppercase: !style.uppercase })}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                style.uppercase ? "bg-purple-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}>
              MAIUSCOLO
            </button>
            <button onClick={() => patch({ bold: !style.bold })}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                style.bold ? "bg-purple-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}>
              <span className="font-bold">Bold</span>
            </button>
            <button onClick={() => patch({ border_style: style.border_style === 3 ? 1 : 3 })}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                style.border_style === 3 ? "bg-purple-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}>
              Box BG
            </button>
          </div>
        </div>

        <button
          onClick={() => { onApply(style); onClose(); }}
          className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 font-semibold transition-colors"
        >
          Applica e re-esporta
        </button>
      </div>
    </div>
  );
}
