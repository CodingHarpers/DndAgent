'use client';

import React, { useState, useEffect } from 'react';
import StatsPanel from '@/components/StatsPanel';
import InventoryPanel from '@/components/InventoryPanel';
import CombatLog from '@/components/CombatLog';

type Scene = {
    scene_id?: string; // Add this
    title: string;
    narrative_text: string;
    available_actions?: string[]; // Make optional
    metadata?: { session_id?: string };
};

export default function PlayPage() {
    const [scene, setScene] = useState<Scene | null>(null);
    const [actionLog, setActionLog] = useState<any>(null);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>("");

    // RPG State
    const [stats, setStats] = useState<any>(null);
    const [inventory, setInventory] = useState<any[]>([]);

    const startSession = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/play/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_name: "Traveler" })
            });
            const data = await res.json();
            setScene(data);
            setActionLog(null);
            const sid = data.metadata?.session_id || data.scene_id || data.session_id; // Check all possible locations
            if (sid) {
                console.log("Session started with ID:", sid);
                setSessionId(sid);
                // Fetch initial RPG state
                await fetchRPGState(sid);
            } else {
                console.error("No session ID found in start_session response", data);
            }
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    const fetchRPGState = async (sid: string) => {
        try {
            const [statsRes, invRes] = await Promise.all([
                fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/play/stats/${sid}`),
                fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/play/inventory/${sid}`)
            ]);
            if (statsRes.ok) setStats(await statsRes.json());
            if (invRes.ok) setInventory(await invRes.json());
        } catch (e) {
            console.error("Failed to fetch RPG state", e);
        }
    };

    const sendAction = async (actionText: string) => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/play/step`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, text: actionText })
            });
            const data = await res.json();
            setScene(data.scene);

            if (data.action_log) {
                setActionLog(data.action_log);
            } else {
                setActionLog(null);
            }

            // Update Stats if returned
            if (data.player_stats) {
                setStats(data.player_stats);
            }
            // Always refresh inventory on turn end
            fetchRPGState(sessionId);

            setInput('');
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col font-sans">
            <header className="p-4 border-b border-gray-700 bg-gray-800 flex justify-between items-center">
                <h1 className="text-xl font-bold tracking-wider text-purple-400">A.R.C.A.N.A.</h1>
                {!scene && (
                    <button
                        onClick={startSession}
                        disabled={loading}
                        className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded"
                    >
                        {loading ? 'Starting...' : 'New Session'}
                    </button>
                )}
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Left: Chat/Scene (60%) */}
                <main className="flex-1 p-6 flex flex-col border-r border-gray-800 overflow-y-auto">
                    {!scene ? (
                        <div className="flex flex-col items-center justify-center flex-grow opacity-50">
                            <p>Start a new session to begin.</p>
                        </div>
                    ) : (
                        <>
                            <div className="flex-grow space-y-6 mb-6">
                                <div className="prose prose-invert max-w-none">
                                    <h2 className="text-2xl text-purple-300 border-b border-gray-700 pb-2 mb-4">
                                        {scene.title}
                                    </h2>

                                    {actionLog && <CombatLog log={actionLog} />}

                                    <p className="text-lg leading-relaxed whitespace-pre-wrap">
                                        {scene.narrative_text}
                                    </p>
                                </div>

                                {scene.available_actions && scene.available_actions.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-4">
                                        {scene.available_actions.map((action, i) => (
                                            <button
                                                key={i}
                                                onClick={() => sendAction(action)}
                                                disabled={loading}
                                                className="text-sm bg-gray-800 hover:bg-gray-700 border border-gray-600 px-3 py-1 rounded-full transition-colors"
                                            >
                                                {action}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="mt-auto">
                                <form
                                    onSubmit={(e) => { e.preventDefault(); sendAction(input); }}
                                    className="flex gap-2"
                                >
                                    <input
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        placeholder="What do you want to do?"
                                        className="flex-grow bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        disabled={loading}
                                    />
                                    <button
                                        type="submit"
                                        disabled={loading || !input.trim()}
                                        className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-semibold"
                                    >
                                        Send
                                    </button>
                                </form>
                            </div>
                        </>
                    )}
                </main>

                {/* Right: RPG Stats (40%) */}
                <aside className="w-[400px] flex-shrink-0 bg-gray-950 p-4 overflow-y-auto flex flex-col gap-6 border-l border-gray-800">
                    {scene && (
                        <>
                            <StatsPanel stats={stats} />
                            <InventoryPanel
                                items={inventory}
                                sessionId={sessionId}
                                onActionComplete={() => fetchRPGState(sessionId)}
                            />
                        </>
                    )}
                </aside>
            </div>
        </div>
    );
}
