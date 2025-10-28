import React from 'react';

interface CombatLogProps {
    log: {
        success: boolean;
        hit?: boolean;
        roll?: number;
        damage?: number;
        target_id?: string;
        target_hp?: number;
        message?: string;
    } | null;
}

export default function CombatLog({ log }: CombatLogProps) {
    if (!log || !log.message) return null;

    const isHit = log.hit === true;
    const isCombat = log.roll !== undefined;

    return (
        <div className={`p-4 rounded-lg border mb-4 shadow-lg ${isHit ? 'bg-red-900/40 border-red-500' : 'bg-gray-800 border-gray-600'}`}>
            <div className="flex items-center justify-between mb-2">
                <span className={`font-bold uppercase tracking-wider ${isHit ? 'text-red-400' : 'text-gray-400'}`}>
                    {isCombat ? 'Combat Log' : 'Action Log'}
                </span>
                {isCombat && (
                    <span className="text-xl font-mono text-yellow-500 font-bold">
                        Roll: {log.roll}
                    </span>
                )}
            </div>

            <p className="text-lg text-gray-200">{log.message}</p>

            {isCombat && log.target_hp !== undefined && (
                <div className="mt-2 text-sm text-gray-400 text-right">
                    Enemy HP: <span className="text-white font-mono">{Math.max(0, log.target_hp)}</span>
                </div>
            )}
        </div>
    );
}
