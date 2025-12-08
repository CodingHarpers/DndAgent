'use client';

import React, { useState } from 'react';

type Scene = {
    title: string;
    narrative_text: string;
    available_actions: string[];
    metadata: { session_id?: string };
};

export default function PlayPage() {
    const [scene, setScene] = useState<Scene | null>(null);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);

    const startSession = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/play/start_session`, {
                method: 'POST'
            });
            const data = await res.json();
            setScene(data.scene);
            setSessionId(data.scene.metadata?.session_id || null);
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
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

            <main className="flex-grow p-6 max-w-3xl mx-auto w-full flex flex-col">
                {!scene ? (
                    <div className="flex flex-col items-center justify-center flex-grow opacity-50">
                        <p>Start a new session to begin.</p>
                    </div>
                ) : (
                    <>
                        <div className="flex-grow space-y-6 overflow-y-auto mb-6">
                            <div className="prose prose-invert max-w-none">
                                <h2 className="text-2xl text-purple-300 border-b border-gray-700 pb-2 mb-4">
                                    {scene.title}
                                </h2>
                                <p className="text-lg leading-relaxed whitespace-pre-wrap">
                                    {scene.narrative_text}
                                </p>
                            </div>

                            {scene.available_actions.length > 0 && (
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
        </div>
    );
}
