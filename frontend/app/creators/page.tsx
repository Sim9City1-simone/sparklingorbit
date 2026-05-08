"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "https://tssogk8cw8884okoo4csg04k.178.104.27.55.sslip.io";

const PLATFORMS = [
  { id: "youtube", label: "YouTube", icon: "▶", color: "text-red-400" },
  { id: "tiktok", label: "TikTok", icon: "♪", color: "text-pink-400" },
  { id: "instagram", label: "Instagram", icon: "◈", color: "text-orange-400" },
];

interface SocialAccount {
  id: string;
  platform: string;
  username: string;
  access_token: string;
}

interface Creator {
  id: string;
  name: string;
  avatar_url: string | null;
  social_accounts: SocialAccount[];
}

interface ConnectFormState {
  creatorId: string;
  platform: string;
  username: string;
  access_token: string;
  refresh_token: string;
  platform_user_id: string;
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

export default function CreatorsPage() {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [newName, setNewName] = useState("");
  const [newAvatar, setNewAvatar] = useState("");
  const [addingCreator, setAddingCreator] = useState(false);
  const [connectForm, setConnectForm] = useState<ConnectFormState | null>(null);
  const [saving, setSaving] = useState(false);

  async function loadCreators() {
    try {
      const r = await fetch(`${BACKEND}/creators`);
      if (r.ok) setCreators(await r.json());
    } catch {}
  }

  useEffect(() => { loadCreators(); }, []);

  async function createCreator(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setSaving(true);
    try {
      const r = await fetch(`${BACKEND}/creators`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim(), avatar_url: newAvatar.trim() || null }),
      });
      if (r.ok) {
        setNewName("");
        setNewAvatar("");
        setAddingCreator(false);
        await loadCreators();
      }
    } finally {
      setSaving(false);
    }
  }

  async function deleteCreator(id: string) {
    if (!confirm("Eliminare questo creator?")) return;
    await fetch(`${BACKEND}/creators/${id}`, { method: "DELETE" });
    await loadCreators();
  }

  async function saveConnection(e: React.FormEvent) {
    e.preventDefault();
    if (!connectForm) return;
    setSaving(true);
    try {
      await fetch(
        `${BACKEND}/creators/${connectForm.creatorId}/social/${connectForm.platform}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            platform: connectForm.platform,
            username: connectForm.username,
            access_token: connectForm.access_token,
            refresh_token: connectForm.refresh_token,
            platform_user_id: connectForm.platform_user_id,
          }),
        }
      );
      setConnectForm(null);
      await loadCreators();
    } finally {
      setSaving(false);
    }
  }

  async function disconnect(creatorId: string, platform: string) {
    await fetch(`${BACKEND}/creators/${creatorId}/social/${platform}`, { method: "DELETE" });
    await loadCreators();
  }

  function openConnect(creator: Creator, platform: string) {
    const existing = creator.social_accounts.find((a) => a.platform === platform);
    setConnectForm({
      creatorId: creator.id,
      platform,
      username: existing?.username ?? "",
      access_token: existing?.access_token ?? "",
      refresh_token: "",
      platform_user_id: "",
    });
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-12 space-y-10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-2xl font-bold hover:opacity-80 transition-opacity">
            ✨ SparklingOrbit
          </Link>
          <p className="text-gray-400 text-sm mt-1">Gestione Creator</p>
        </div>
        <div className="flex gap-4 text-sm text-gray-400">
          <Link href="/history" className="hover:text-white transition-colors">Storico</Link>
          <Link href="/" className="hover:text-white transition-colors">← Home</Link>
        </div>
      </div>

      {/* Creator list */}
      <section className="space-y-4">
        {creators.length === 0 && !addingCreator && (
          <p className="text-gray-500 text-sm text-center py-8">
            Nessun creator ancora. Aggiungine uno!
          </p>
        )}

        {creators.map((creator) => (
          <div
            key={creator.id}
            className="bg-gray-900 rounded-2xl border border-gray-800 p-5 space-y-4"
          >
            {/* Creator header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {creator.avatar_url ? (
                  <img
                    src={creator.avatar_url}
                    alt={creator.name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <span className="w-10 h-10 rounded-full bg-purple-700 flex items-center justify-center font-bold text-sm">
                    {initials(creator.name)}
                  </span>
                )}
                <span className="font-semibold">{creator.name}</span>
              </div>
              <button
                onClick={() => deleteCreator(creator.id)}
                className="text-gray-600 hover:text-red-400 text-xs transition-colors"
              >
                Elimina
              </button>
            </div>

            {/* Platform connections */}
            <div className="grid grid-cols-3 gap-3">
              {PLATFORMS.map((p) => {
                const account = creator.social_accounts.find((a) => a.platform === p.id);
                return (
                  <div
                    key={p.id}
                    className={`rounded-xl border p-3 space-y-2 transition-colors ${
                      account
                        ? "border-green-800 bg-green-950/30"
                        : "border-gray-800 bg-gray-800/30"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-sm font-medium flex items-center gap-1.5 ${p.color}`}>
                        <span>{p.icon}</span>
                        {p.label}
                      </span>
                      {account && (
                        <span className="text-xs text-green-400">✓</span>
                      )}
                    </div>

                    {account ? (
                      <div className="space-y-1.5">
                        <p className="text-xs text-gray-400 truncate">
                          @{account.username || "connesso"}
                        </p>
                        <div className="flex gap-1">
                          <button
                            onClick={() => openConnect(creator, p.id)}
                            className="flex-1 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 text-xs transition-colors"
                          >
                            Modifica
                          </button>
                          <button
                            onClick={() => disconnect(creator.id, p.id)}
                            className="py-1 px-2 rounded-lg bg-gray-800 hover:bg-red-900/50 text-xs text-gray-500 hover:text-red-400 transition-colors"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => openConnect(creator, p.id)}
                        className="w-full py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-xs font-medium transition-colors"
                      >
                        Collega
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </section>

      {/* Add creator form */}
      {addingCreator ? (
        <form
          onSubmit={createCreator}
          className="bg-gray-900 rounded-2xl border border-gray-800 p-5 space-y-4"
        >
          <h3 className="font-semibold text-sm text-gray-300">Nuovo Creator</h3>
          <input
            type="text"
            placeholder="Nome creator"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
            className="w-full px-4 py-2.5 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm"
          />
          <input
            type="url"
            placeholder="URL avatar (opzionale)"
            value={newAvatar}
            onChange={(e) => setNewAvatar(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm font-semibold transition-colors"
            >
              {saving ? "Salvo..." : "Crea Creator"}
            </button>
            <button
              type="button"
              onClick={() => setAddingCreator(false)}
              className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-sm transition-colors"
            >
              Annulla
            </button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setAddingCreator(true)}
          className="w-full py-3 rounded-2xl border border-dashed border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-400 text-sm font-medium transition-all"
        >
          + Aggiungi Creator
        </button>
      )}

      {/* Connect modal */}
      {connectForm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 px-4">
          <div className="bg-gray-900 rounded-2xl w-full max-w-sm p-6 space-y-4 border border-gray-800">
            <div className="flex justify-between items-center">
              <h2 className="font-bold text-lg capitalize">
                Collega {connectForm.platform}
              </h2>
              <button
                onClick={() => setConnectForm(null)}
                className="text-gray-500 hover:text-white text-xl"
              >
                ✕
              </button>
            </div>

            <form onSubmit={saveConnection} className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Username</label>
                <input
                  type="text"
                  placeholder="@username"
                  value={connectForm.username}
                  onChange={(e) =>
                    setConnectForm((f) => f && { ...f, username: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Access Token</label>
                <input
                  type="text"
                  placeholder="Incolla il token..."
                  value={connectForm.access_token}
                  onChange={(e) =>
                    setConnectForm((f) => f && { ...f, access_token: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">
                  User ID (opzionale)
                </label>
                <input
                  type="text"
                  placeholder="Platform user ID"
                  value={connectForm.platform_user_id}
                  onChange={(e) =>
                    setConnectForm((f) => f && { ...f, platform_user_id: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-xl bg-gray-800 border border-gray-700 focus:outline-none focus:border-purple-500 text-white placeholder-gray-500 text-sm"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm font-semibold transition-colors"
              >
                {saving ? "Salvo..." : "Salva Connessione"}
              </button>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
