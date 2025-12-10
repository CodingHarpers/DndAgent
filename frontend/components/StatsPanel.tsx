import React from 'react';

interface StatsProps {
    stats: {
        hp_current: number;
        hp_max: number;
        gold: number;
        power: number;
        speed: number;
    } | null;
}

export default function StatsPanel({ stats }: StatsProps) {
    if (!stats) return <div className="p-4 rounded bg-gray-900 border border-gray-700 text-gray-400">Loading Stats...</div>;

    const hpPercent = Math.min((stats.hp_current / stats.hp_max) * 100, 100);

    return (
        <div className="p-4 rounded-lg bg-gray-900 border border-gray-700 space-y-4">
            <h3 className="text-xl font-bold text-gray-200 uppercase tracking-widest border-b border-gray-700 pb-2">Character Status</h3>

            {/* Health Bar */}
            <div>
                <div className="flex justify-between text-sm mb-1 text-gray-400">
                    <span>Health</span>
                    <span>{stats.hp_current} / {stats.hp_max}</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                    <div
                        className="bg-red-600 h-full transition-all duration-500 ease-out"
                        style={{ width: `${hpPercent}%` }}
                    />
                </div>
            </div>

            {/* Grid Stats */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-2 rounded text-center border border-gray-700">
                    <div className="text-xs text-gray-500 uppercase">Power</div>
                    <div className="text-xl font-mono text-blue-400">{stats.power}</div>
                </div>
                <div className="bg-gray-800 p-2 rounded text-center border border-gray-700">
                    <div className="text-xs text-gray-500 uppercase">Speed</div>
                    <div className="text-xl font-mono text-green-400">{stats.speed}</div>
                </div>
            </div>

            {/* Gold */}
            <div className="flex items-center justify-between bg-yellow-900/20 p-3 rounded border border-yellow-800/50">
                <span className="text-yellow-500 font-bold">GOLD</span>
                <span className="text-yellow-400 font-mono text-lg">{stats.gold} gp</span>
            </div>
        </div>
    );
}
