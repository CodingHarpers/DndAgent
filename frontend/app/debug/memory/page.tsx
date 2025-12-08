'use client';

import React, { useState, useEffect } from 'react';

export default function MemoryDebugPage() {
    const [sessionID, setSessionID] = useState<string>('');
    const [memories, setMemories] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchMemory = async () => {
        if (!sessionID) return;
        setLoading(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/debug/session/${sessionID}/memory`);
            if (res.ok) {
                const data = await res.json();
                setMemories(data);
            }
        } catch (e) {
            console.error(e);
        }
        setLoading(false);
    };

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold mb-4">Memory Inspector</h1>
            <div className="flex gap-2 mb-6">
                <input
                    type="text"
                    placeholder="Session ID"
                    value={sessionID}
                    onChange={(e) => setSessionID(e.target.value)}
                    className="border p-2 rounded flex-grow text-black"
                />
                <button
                    onClick={fetchMemory}
                    className="bg-blue-600 text-white px-4 py-2 rounded"
                >
                    Inspect
                </button>
            </div>

            {loading && <p>Loading...</p>}

            <div className="space-y-4">
                {memories.map((mem, idx) => (
                    <div key={idx} className="border p-4 rounded bg-gray-50 text-black">
                        <div className="font-semibold text-sm text-gray-500">{mem.timestamp}</div>
                        <div>{mem.summary}</div>
                        <pre className="text-xs mt-2 bg-gray-200 p-2 overflow-auto">
                            {JSON.stringify(mem, null, 2)}
                        </pre>
                    </div>
                ))}
                {memories.length === 0 && !loading && (
                    <p className="text-gray-500">No memories found or ID not set.</p>
                )}
            </div>
        </div>
    );
}
