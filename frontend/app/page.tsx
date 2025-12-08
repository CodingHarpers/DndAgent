import Link from 'next/link';

export default function Home() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-950 text-white p-4">
            <div className="max-w-2xl text-center space-y-8">
                <h1 className="text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
                    A.R.C.A.N.A.
                </h1>
                <p className="text-xl text-gray-400">
                    Agentic Rules-based & Creative Autonomous Narrative Architecture
                </p>
                <div className="flex justify-center gap-4">
                    <Link href="/play" className="bg-white text-black px-8 py-3 rounded-full font-bold hover:bg-gray-200 transition-colors">
                        Start Playing
                    </Link>
                    <Link href="/debug/memory" className="border border-gray-600 px-8 py-3 rounded-full font-bold hover:bg-gray-800 transition-colors">
                        Debug Memory
                    </Link>
                </div>
            </div>
        </div>
    );
}
