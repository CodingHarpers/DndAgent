import React, { useState } from 'react';

interface Item {
    id: string;
    name: string;
    type: string;
    properties: any;
}

interface InventoryProps {
    items: Item[];
    sessionId: string;
    onActionComplete: () => void; // Callback to refresh stats
}

export default function InventoryPanel({ items, sessionId, onActionComplete }: InventoryProps) {
    const [buyId, setBuyId] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // For demo, we might want a quick "debug buy" field since we don't have a shop UI yet.
    // Or we just display inventory here. 
    // Let's assume this is strictly "Backpack".
    // Note: The user asked for "Buying an item checks... balance".
    // We need a way to trigger buying. 
    // Let's add a simple "Purchase Item by ID" input for testing/demo purposes 
    // until a real Shop component exists.

    const handleBuy = async () => {
        if (!buyId) return;
        setLoading(true);
        setError("");
        try {
            const res = await fetch('/api/play/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, item_id: buyId })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to buy");

            setBuyId("");
            onActionComplete(); // Refresh parent
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 rounded-lg bg-gray-900 border border-gray-700 space-y-4">
            <h3 className="text-xl font-bold text-gray-200 uppercase tracking-widest border-b border-gray-700 pb-2">Backpack</h3>

            {/* Item List */}
            <div className="space-y-2 max-h-60 overflow-y-auto">
                {items.length === 0 ? (
                    <div className="text-gray-500 italic text-center py-4">Empty</div>
                ) : (
                    items.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-700">
                            <div>
                                <div className="font-bold text-gray-300">{item.name}</div>
                                <div className="text-xs text-gray-500">{item.type}</div>
                            </div>
                            {/* Future: Equip button */}
                        </div>
                    ))
                )}
            </div>

            {/* Debug Buy Input */}
            <div className="pt-4 border-t border-gray-700">
                <label className="block text-xs text-gray-500 mb-1">Mercantile Channel (Debug Buy)</label>
                <div className="flex space-x-2">
                    <input
                        type="text"
                        placeholder="Item ID (e.g. item_rusty_sword)"
                        className="flex-1 bg-gray-950 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
                        value={buyId}
                        onChange={(e) => setBuyId(e.target.value)}
                    />
                    <button
                        onClick={handleBuy}
                        disabled={loading}
                        className="px-3 py-1 bg-blue-700 hover:bg-blue-600 text-white rounded text-xs font-bold transition-colors disabled:opacity-50"
                    >
                        BUY
                    </button>
                </div>
                {error && <div className="text-red-500 text-xs mt-1">{error}</div>}
            </div>
        </div>
    );
}
