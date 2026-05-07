"use client";

import { useState } from "react";

export interface CaptionStyle {
  highlight_color: string;
  text_color: string;
  outline_color: string;
  font_size: number;
  position: "bottom" | "center" | "top";
}

const DEFAULT: CaptionStyle = {
  highlight_color: "FFFF00",
  text_color: "FFFFFF",
  outline_color: "000000",
  font_size: 52,
  position: "bottom",
};

const PRESETS: { label: string; style: CaptionStyle }[] = [
  { label: "Classic", style: { ...DEFAULT } },
  {
    label: "Fire",
    style: { ...DEFAULT, highlight_color: "FF4500", text_color: "FFFFFF" },
  },
  {
    label: "Neon",
    style: { ...DEFAULT, highlight_color: "00FFFF", text_color: "FFFFFF" },
  },
  {
    label: "White",
    style: { ...DEFAULT, highlight_color: "FFFFFF", text_color: "CCCCCC" },
  },
];

interface Props {
  onApply: (style: CaptionStyle) => void;
  onClose: () => void;
}

function HexColorInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-sm text-gray-400 w-28 shrink-0">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={`#${value}`}
          onChange={(e) => onChange(e.target.value.replace("#", "").toUpperCase())}
          className="w-8 h-8 rounded cursor-pointer bg-transparent border-0"
        />
        <span className="text-xs font-mono text-gray-400">#{value}</span>
      </div>
    </div>
  );
}

export default function CaptionStylePicker({ onApply, onClose }: Props) {
  const [style, setStyle] = useState<CaptionStyle>(DEFAULT);

  function patch(partial: Partial<CaptionStyle>) {
    setStyle((s) => ({ ...s, ...partial }));
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-sm p-6 space-y-5 border border-gray-800">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold">Stile Caption</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl">
            ✕
          </button>
        </div>

        {/* Presets */}
        <div className="grid grid-cols-4 gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => setStyle(p.style)}
              className="py-1.5 rounded-lg text-xs font-medium bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Colors */}
        <div className="space-y-3">
          <HexColorInput
            label="Parola attiva"
            value={style.highlight_color}
            onChange={(v) => patch({ highlight_color: v })}
          />
          <HexColorInput
            label="Testo"
            value={style.text_color}
            onChange={(v) => patch({ text_color: v })}
          />
          <HexColorInput
            label="Contorno"
            value={style.outline_color}
            onChange={(v) => patch({ outline_color: v })}
          />
        </div>

        {/* Font size */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm text-gray-400">
            <span>Dimensione testo</span>
            <span className="font-mono">{style.font_size}px</span>
          </div>
          <input
            type="range"
            min={32}
            max={80}
            value={style.font_size}
            onChange={(e) => patch({ font_size: Number(e.target.value) })}
            className="w-full accent-purple-500"
          />
        </div>

        {/* Position */}
        <div className="flex gap-2">
          {(["bottom", "center", "top"] as const).map((pos) => (
            <button
              key={pos}
              onClick={() => patch({ position: pos })}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                style.position === pos
                  ? "bg-purple-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {pos}
            </button>
          ))}
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
